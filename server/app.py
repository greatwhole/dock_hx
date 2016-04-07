# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import re
import sys
import inspect
import warnings

import argparse

from ..common.globals import config, statsd
from ..common import log, tracebackturbo
from ..common.app import DockEnv
from ..common.exceptions import SessionError, RequestDataException, AppBaseException
from flask import Flask, Blueprint, request, g, json, jsonify, after_this_request
from werkzeug.exceptions import HTTPException

import base64
import time
import hmac
import hashlib

from werkzeug.exceptions import HTTPException

class AppIsNotMountableException(Exception):
    pass

logger = log.get_logger()


usage = """Dock Application Server.

Usage:
  server.py <command> [<args>...]
  server.py (-h | --help)

Options:
  -h --help      Show this screen.

The most commonly used git commands are:
   runserver        Run web server.
   initdb           Init dynamo tables.
   runcommand       Run shell command.
   runtask          Load and Run tasklet.
"""

runserver_usage = """Dock Application Server.

Usage:
  server.py runserver [--host=<host>] [--port=<port>]
  server.py runserver (-h | --help)

Options:
  -h --help      Show this screen.
  --host <host>  Host [default: 0.0.0.0].
  --port <port>  Port [default: 5000].
"""

initdb_usage = """Dock Application Server.

Usage:
  server.py initdb
  server.py initdb (-h | --help)
"""


class DockApp(DockEnv):
    def __init__(self, name_or_app, config_file="config.yaml"):
        if isinstance(name_or_app, Flask):
            import_name = name_or_app.import_name
            self.app = name_or_app
        else:
            import_name = name_or_app
            self.app = Flask(name_or_app)
        if os.path.isabs(config_file):
            self.config_file = config_file
        else:
            self.config_file = os.path.join(self.app.root_path, config_file)
        super(DockApp, self).__init__(import_name, config_file = self.config_file)

    @property
    def flaskapp(self):
        return self.app

    def init_app(self):
        self.app.config.update(config)
        self.app.log = logger
        self.log = log.get_logger('api')
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
        self.app.teardown_request(self.teardown_request)
        self.app.register_error_handler(Exception, self.error_handler)

        for code in [400, 401, 402, 403, 404, 405, 406, 408, 409, 410, 411, 412, 413, 414,
            415, 416, 417, 418, 422, 428, 429, 431, 500, 501, 502, 503, 504, 505]:
            self.app.register_error_handler(code, self.error_handler)


    def verify_signature(self, key_version, signature, content):
        request_config = config.get('main', {}).get('request', {})
        sig_keys = request_config.get('sig_keys')
        key = sig_keys.get(str(key_version))
        if not key:
            return False
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        sig = hmac.new(key, content, hashlib.sha256).hexdigest()
        return sig == signature

    def before_request(self):
        logger.debug('REQUEST', ('url', request.base_url), ('endpoint', request.endpoint))
        g.rawdata = request.get_data(cache=True, parse_form_data=False)
        g.jsondata = {}
        if request.endpoint is None:
            return
        g.request_started = time.time()
        g.statsd_key = request.endpoint

        self.log.debug('REQUEST', ('values', json.dumps(request.values.to_dict())))
        content = request.values.get('content')
        signature = request.values.get('signature', '')
        sig_kv = request.values.get('sig_kv')

        if content:
            if not self.verify_signature(sig_kv, signature, content):
                raise RequestDataException('Signature Not Correct.')

            try:
                g.jsondata = json.loads(content)
            except:
                pass
        self.log.debug('REQUEST', 'jsondata: %s' % (g.jsondata))

    def teardown_request(self, exc):
        if exc:
            self.log.error('SHOULD_NOT_HAPPEN','teardown_request, has exception:%s'%(exc))

    def after_request(self, response):
        if request.endpoint is None:
            return response

        if response is None:
            return response

        code = -1

        if getattr(g, 'request_started', None) is not None:
            t = (time.time() - g.request_started)*1000
            if getattr(g, 'response_code', None) is None:
                code = response.status_code
            else:
                code = g.response_code
            key_mapping = {
                2: 'ok',
                4: '4xx',
                5: '5xx',
            }
            keys = ['api.%s.%s'%(g.statsd_key, key_mapping.get(code/100, 'unknown')),
                    'api.all.%s'%(key_mapping.get(code/100, 'unknown')),
                    'api.%s.cost'%(g.statsd_key),
                    'api.all.cost']
            for key in keys[:2]:
                statsd.incr(key)
            if code/100 == 2:
                for key in keys[2:]:
                    statsd.timing(key, int(t))
                if t > config.request_slow_timeout:
                    request_data = getattr(g, 'jsondata', None)
                    self.log.captureMessage('Slow request of %s%s'%(request.script_root, request.path),
                        request_url=request.url, request_data=request_data, extra={'request_cost': t})
        self.log_request(response, code)
        return response

    def error_handler(self, error):

        request_data = getattr(g, 'jsondata', None)
        if not isinstance(error, AppBaseException):
            self.log.captureException(request_url=request.url, request_data=request_data)

        self.log.error('EXCEPTION', 'response_error', sys.exc_info()[1],
                       getattr(error, "description", ""), locals())
        self.log.error('TRACEBACK', tracebackturbo.format_exc())

        if isinstance(error, SessionError):
            statsd.incr('api.all.error.session_error')

        return self.response_error(error)

    def response_error(self, error):
        if isinstance(error, HTTPException):
            g.response_code = error.code
            meta = {'code': error.code, 'error_type':error.__class__.__name__,'error_message':error.description}
            if getattr(error, 'extra_info', None):
                meta.update(error.extra_info)
            if error.response and isinstance(error.response, dict):
                return jsonify(meta=meta, data=error.response)
            else:
                return jsonify(meta=meta)
        else:
            g.response_code = 500
            return jsonify(meta = {'code': 500, 'error_type':error.__class__.__name__, 'error_message':unicode(error)})


    def log_request(self, response, code=200):
        self.log.info('request', request.remote_addr, request.method,
            request.script_root + request.path, request.headers.get('Content-Length', '0'),
            response.status_code, code, str(response.headers.get('Content-Length', '0')))

    def mount(self, block, mapping={}, skiplist=[]):
        block_name =  block.__class__.__name__
        if block_name == 'module':
            block_name = block.__name__
        logger.info('MOUNT_BLOCK', block_name)
        initfunc = getattr(block, 'init', None)
        if initfunc is  None or not callable(initfunc):
            raise Exception('%s does not have callable init func'%(block))
        blueprints = initfunc(self.app)
        toskips = set(skiplist)
        for bp in blueprints:
            if bp.name in mapping:
                url_prefix = '%s%s'%(mapping[bp.name], bp.url_prefix or '')
            else:
                url_prefix = bp.url_prefix

            logger.info('MOUNT_BLUEPRINT', ('name', bp.name), ('url_prefix', url_prefix),
                ('skip', bp.name in toskips))
            if bp.name in toskips:
                continue
            self._mount(bp, url_prefix)

    def get_remote_addr(self, forwarded_for, num_proxies=1):
        if len(forwarded_for) >= num_proxies:
            return forwarded_for[-1 * num_proxies]

    def __call__(self, environ, start_response):
        """Shortcut for :attr:`wsgi_app`."""
        getter = environ.get
        forwarded_proto = getter('HTTP_X_FORWARDED_PROTO', '')
        forwarded_for = getter('HTTP_X_FORWARDED_FOR', '').split(',')
        forwarded_host = getter('HTTP_X_FORWARDED_HOST', '')
        environ.update({
            'werkzeug.proxy_fix.orig_wsgi_url_scheme':  getter('wsgi.url_scheme'),
            'werkzeug.proxy_fix.orig_remote_addr':      getter('REMOTE_ADDR'),
            'werkzeug.proxy_fix.orig_http_host':        getter('HTTP_HOST')
        })
        forwarded_for = [x for x in [x.strip() for x in forwarded_for] if x]
        remote_addr = self.get_remote_addr(forwarded_for, config.num_proxies)
        if remote_addr is not None:
            environ['REMOTE_ADDR'] = remote_addr
        if forwarded_host:
            environ['HTTP_HOST'] = forwarded_host
        if forwarded_proto:
            environ['wsgi.url_scheme'] = forwarded_proto
        return self.flaskapp(environ, start_response)


    def _mount(self, obj, url_prefix):
        if isinstance(obj, Blueprint):
            self.app.register_blueprint(obj, url_prefix=url_prefix)
        else:
            raise AppIsNotMountableException('%s is not mountable, must be Blueproint'%(obj))


    def run_server(self):
        from docopt import docopt
        arguments = docopt(runserver_usage, help=True)

        from werkzeug.serving import run_simple
        options = {}
        options.setdefault('use_reloader', True)
        options.setdefault('use_debugger', True)

        run_simple(arguments['--host'], int(arguments['--port']), self, **options)

    def run_initdb(self):
        from docopt import docopt
        arguments = docopt(initdb_usage, help=True)

        from ..redynadb import redyna_manager
        redyna_manager.init_models()
        return 0


    def run_command(self):
        from commandr import Run
        sys.argv.pop(1)
        return Run()


    def run_task(self):
        from ..common.tasklet import run_tasklet
        sys.argv.pop(1)
        task_conf = {}
        for name, value in config.items():
            if 'tasklet' in value:
                for name, param in value['tasklet'].items():
                    param.update(name=name)
                    task_conf[name] = param
        run_tasklet('runtask', task_conf)

    def run(self):
        """
        Prepares manager to receive command line input. Usually run
        inside "if __name__ == "__main__" block in a Python script.
        """

        if len(sys.argv) == 1:
            print(usage)
            sys.exit(0)

        command = sys.argv[1].lower()
        funcs = {
            'runserver': self.run_server,
            'initdb': self.run_initdb,
            'runcommand': self.run_command,
            'runtask': self.run_task,
        }
        func = funcs.get(command)

        if not func:
            if command not in ['-h', '--help']:
                print('Command %s is not supported\n'%(command))
            print(usage)
            sys.exit(-1)
        sys.exit(func())

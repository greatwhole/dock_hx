# -*- encoding: utf-8 -*-

from logging import getLogger
import threading
import user_agents
from django.http import HttpResponseRedirect, QueryDict
from django.conf import settings
from . import consts


logger = getLogger(__name__)

_thread_locals = threading.local()

def get_request():
    return getattr(_thread_locals, 'request', None)


class RedirectMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.


    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        user_agents_str = request.META['HTTP_USER_AGENT']
        url = request.build_absolute_uri()
        user_agent = user_agents.parse(user_agents_str)
        is_mobile = user_agent.is_mobile

        logger.debug('is_mobile={}'.format(is_mobile))


        # 开发模式下，如果是用127.0.0.1:8000访问的，则只在url的querystring中加入flavor=mobile
        # TODO 考虑port不是80？
        flag_use_flavor = '8000' in request.META['HTTP_HOST'] and settings.DEBUG is True

        flavour = request.GET.get(consts.FLAVOUR_NAME, consts.PC)

        need_redirect = False

        if flag_use_flavor:
            query_string = request.META['QUERY_STRING']

            qd = QueryDict(query_string=query_string, mutable=True)

            if is_mobile and flavour == consts.PC:
                need_redirect = True
                qd[consts.FLAVOUR_NAME] = consts.MOBILE

            elif (not is_mobile) and flavour == consts.MOBILE:
                need_redirect = True
                qd.pop(consts.FLAVOUR_NAME, None)

            elif flavour not in [consts.PC, consts.MOBILE]:
                raise Exception('illegal flavour')

            logger.debug('flag_can_not_redirect|need_redirect={}'.format(need_redirect))

            if need_redirect:
                request.META['QUERY_STRING'] = qd.urlencode()
                new_url = request.build_absolute_uri()
                logger.debug('flag_can_not_redirect|new_url={}'.format(new_url))
                return HttpResponseRedirect(new_url)
            else:
                return

        new_url = url
        if user_agent.is_mobile and '//m.' not in url:
            if '//www.' in url:
                new_url = url.replace('//www.', '//m.')
            else:
                new_url = url.replace('//', '//m.')
        elif not user_agent.is_mobile and '//m.' in url:
            new_url = url.replace('//m.', '//')

        if new_url != url:
            logger.debug(u'user_agent: {}.old url: {}. new url: {}.'.format(user_agents_str, url, new_url))
            return HttpResponseRedirect(new_url)


class StoreRequestMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        _thread_locals.request = request

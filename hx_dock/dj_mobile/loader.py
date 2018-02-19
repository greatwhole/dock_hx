# -*- encoding: utf-8 -*-

from django.template import TemplateDoesNotExist, Engine
from django.template.loaders.base import Loader

from .middleware import get_request
from .alter_url import is_target_mobile
from . import consts
from logging import getLogger
import traceback


logger = getLogger(__name__)


class HxLoader(Loader):
    _template_source_loaders = None

    @property
    def template_source_loaders(self):
        if not self._template_source_loaders:
            loaders = []
            # for loader_name in settings.FLAVOURS_TEMPLATE_LOADERS:
            for loader_name in ['django.template.loaders.app_directories.Loader']:
                loader = Engine.get_default().find_template_loader(loader_name)
                if loader is not None:
                    loaders.append(loader)
            self._template_source_loaders = tuple(loaders)
        return self._template_source_loaders

    def get_template(self, template_name, template_dirs=None, skip=None):
        try:
            return super(HxLoader, self).get_template(template_name=template_name, template_dirs=template_dirs, skip=skip)
        except TemplateDoesNotExist as e:
            new_template_name = self.prepare_template_name(template_name)
            logger.error('template not found. template_name: <%s>' % new_template_name)
            raise TemplateDoesNotExist(new_template_name, e.tried)

    def get_template_sources(self, template_name):
        new_template_name = self.prepare_template_name(template_name)
        for loader in self.template_source_loaders:
            if hasattr(loader, 'get_template_sources'):
                try:
                    for result in loader.get_template_sources(new_template_name):
                        yield result
                except UnicodeDecodeError:
                    # The template dir name was a bytestring that wasn't valid UTF-8.
                    raise
                except ValueError:
                    # The joined path was located outside of this particular
                    # template_dir (it might be inside another one, so this isn't
                    # fatal).
                    pass

    def load_template_source(self, template_name, template_dirs=None):
        new_template_name = self.prepare_template_name(template_name)
        for loader in self.template_source_loaders:
            if hasattr(loader, 'load_template_source'):
                try:
                    return loader.load_template_source(
                        new_template_name,
                        template_dirs)
                except TemplateDoesNotExist:
                    pass
        raise TemplateDoesNotExist("Tried %s" % new_template_name)

    def prepare_template_name(self, template_name):

        try:
            request = get_request()
            if request is None:
                new_template_name = template_name

            else:
                url = request.build_absolute_uri()
                arg_is_mobile = request.GET.get(consts.FLAVOUR_NAME, consts.PC) == consts.MOBILE
                logger.debug('arg_is_mobile={}'.format(arg_is_mobile))

                dir_, filename = template_name.split('/')
                if (is_target_mobile(url) or arg_is_mobile )and '_m' not in dir_:
                    new_template_name = '{}_m/{}'.format(dir_, filename)
                    logger.info('redirect. from %s to %s' % (template_name, new_template_name))
                else:
                    new_template_name = template_name
        except (ValueError, ) as e:
            new_template_name = template_name
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            new_template_name = template_name

        return new_template_name

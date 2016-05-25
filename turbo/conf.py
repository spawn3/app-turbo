from __future__ import absolute_import, division, print_function, with_statement

import os
from copy import deepcopy
import tornado.web
import tornado.httpserver
import tornado.escape
import tornado.ioloop
from tornado.options import define, options
from tornado.util import ObjectDict


from turbo.log import app_log
from turbo.util import join_sys_path, get_base_dir, import_object


def _install_app(package_space):
    for app in getattr(import_object('apps.settings', package_space), 'INSTALLED_APPS'):
       _ = import_object('.'.join(['apps', app]), package_space)


class ErrorHandler(tornado.web.RequestHandler):

    def initialize(self, status_code):
        self.set_status(status_code)

    def prepare(self):
        t = tornado.template.Template('<h1>{{error_code}}</h1>')
        self.write(t.generate(error_code=self._status_code))
        self.finish()


class ObjectDict(dict):
    """Makes a dictionary behave like an object, with attribute-style access.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class AppConfig(object):

    _cookie_session_config = ObjectDict(
        name='session_id',
        cookie_domain=None,
        cookie_path='/',
        cookie_expires=86400,  # cookie expired  24 hours in seconds
        secure = True,
        secret_key='fLjUfxqXtfNoIldA0A0J', # generate session id,
        timeout=86400, # session timeout 24 hours in seconds
    )

    _store_config = ObjectDict(
        diskpath='/tmp/session',
    )

    def __init__(self):
        self.app_name = ''
        self.urls = []
        self.error_handler = None
        self.app_setting = {}
        self.web_application_setting = {}
        self.project_name = None
        self.session_config = self._cookie_session_config
        self.store_config = self._store_config

    @property
    def log_level(self):
        import logging
        level = self.app_setting.get('log', {}).get('log_level')
        if level is None:
            return logging.INFO

        return level

    def register_app(self, app_name, app_setting, web_application_setting, mainfile, package_space):
        from turbo import log
        self.app_name = app_name
        self.app_setting = app_setting
        self.project_name = os.path.basename(get_base_dir(mainfile, 2))
        self.web_application_setting = web_application_setting
        if app_setting.get('session_config'):
            self.session_config.update(app_setting['session_config'])
        log.getLogger(**app_setting.log)
        _install_app(package_space)
        pass

    def register_urls(self, prefix, urls):
        def add_prefix(tup):
            lst = list(tup)
            lst[0] = prefix + lst[0]
            return tuple(lst)

        urls = [add_prefix(tup) for tup in urls]
        self.urls.extend(urls)

    def start(self, port):
        app_log.info(self.app_name+' app start')
        self.error_handler = self.error_handler if self.error_handler else ErrorHandler
        tornado.web.ErrorHandler = self.error_handler
        application = tornado.web.Application(self.urls, **self.web_application_setting)
        http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
        http_server.listen(port)
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.start()


app_config = AppConfig()

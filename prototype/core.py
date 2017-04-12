from jinja2 import (Environment, FileSystemLoader,
                    TemplateSyntaxError,
                    TemplateAssertionError,
                    UndefinedError,
                    TemplateNotFound,
                    TemplatesNotFound)
from translations import TranslationManager
from error import ErrorRenderer
from tornado.web import Application, RequestHandler, StaticFileHandler
import tornado.autoreload
import tornado.ioloop
import pylibsass
import os
import sys
import shutil
import json
import random
import socket
import errno
import traceback
import gettext
import urlparse


JINJA_GENERIC_EXCEPTION = (UndefinedError, TemplateNotFound, TemplatesNotFound)
JINJA_DETAILED_EXCEPTION = (TemplateSyntaxError, TemplateAssertionError)


class Prototype(object):
    def __init__(self):
        self.project_path = os.getcwd()
        self.source_path = os.path.join(self.project_path, 'source')
        self.build_path = os.path.join(self.project_path, 'build')
        self.template_path = os.path.join(self.project_path, 'source', 'layouts')

        try:
            config_path = os.path.join(self.project_path, 'config.json')
            config = open(config_path, 'r')
            self.config = json.load(config)
        except Exception as e:
            print 'Fatal Error: config.json missing or corrupt.'
            raise

        self.translations_key = self.config.get('translations_key', '')
        self.port = self.config.get('port', 2000)


        # create static file handlers for all sub folders of the source directory
        # a static file handler has the following format
        #
        # (r"/css/(.*)", StaticFileHandler, {"path": os.path.join(self.source_path, 'css')})
        handlers = []
        level = 1
        for root, folders, files in os.walk(self.source_path):
            if level > 0:
                for folder in folders:
                    handlers.append(
                        (
                            r"/%s/(.*)" % (folder), 
                            StaticFileHandler, 
                            {"path": os.path.join(self.source_path, folder)}
                        )
                    )
            else:
                break
            level-=1

        handlers += [
            (r"/(?P<language>[a-z]{2}|[a-z]{2}_[A-Z]{2})/.*", TranslatedHandler),
            (r"/.*", DefaultHandler),
        ]

        # set up tornado web application
        self.application = Application(handlers)

        # set up jinja template loader
        template_loader = FileSystemLoader(searchpath=self.source_path)
        self.jinja_environment = Environment(
            loader=template_loader,
            extensions=['jinja2.ext.i18n'],
        )

        self.jinja_environment.globals['asset'] = self.asset


    def runserver(self, port=None):
        """
        run the tornado web server and watch for sass changes
        """
        # changed from: if port == None:
        if port is None:
            port = self.port

        try:
            # watch for sass changes
            pylibsass.watch(
                os.path.join(self.source_path, 'scss'),
                os.path.join(self.source_path, 'css')
            )

            # setup the server
            tornado.autoreload.add_reload_hook(self.reload_hook)
            tornado.autoreload.start()
            self.application.listen(port)

            print 'now serving on port 127.0.0.1:%s...' % port
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt as e:
            pass
        except socket.error:
            print 'port %s is already in use.' % (port)


    def asset(self, filename, cachebuster=False):
        """
        for jinja templates, returns the asset specified and
        optionally applies the cachebuster
        """
        if cachebuster:
            return filename + '?ver=' + str(random.getrandbits(10))
        else:
            return filename

    def full_asset_path(self, filename, cachebuster=False):
        """
        Returns the absolute file path of an asset
        """
        if self.config.get('build_path') or self.config.get('build_path') == '':
            path = self.config['build_path']
        else:
            path = self.current_path
 
        if filename[0] == '/':
            filename = filename[1:]
        return os.path.join(path, filename)


    def render_html(self, uri, **kwargs):
        """
        returns HTML document as a string
        """
        print 'Render HTML :: {}'.format(uri)

        path = self.source_path
        language = kwargs.get('language', False)
        build = kwargs.get('build', False)

        # load the translations
        try:
            if language:
                language = [language.replace('-', '_')]
                locale_path = os.path.join(self.project_path, 'translations')
                translations_path = gettext.find(self.translations_key,
                                                 locale_path, language)
                translations = gettext.translation(self.translations_key,
                                                   locale_path, language,
                                                   fallback=False)
            else:
                translations = False
        except Exception as e:
            self.handle_generic_exception(e, 'Error loading translations')

        # try to get rendered HTML
        try: 
            if build:
                path = self.build_path
                if language:
                    path = os.path.join(path, language[0])

            self.current_path = path

            if build:
                self.jinja_environment.globals['asset'] = self.full_asset_path
            if translations:
                self.jinja_environment.install_gettext_translations(translations, newstyle=True)
            else:
                self.jinja_environment.install_null_translations()

            # load the file
            template_file = uri.replace(path, '')
            try:
                template = self.jinja_environment.get_template(template_file)
            except TemplateNotFound as e:
                print 'Cannot locate template {}'.format(template_file)
                return ''

            # load data from data folder into custom_data dictionary
            custom_data = {}
            for root, folders, files in os.walk(os.path.join(self.project_path, self.config['data']), topdown=False):
                for name in files:
                    try:
                        fe = open(os.path.join(root, name))
                        loaded = json.load(fe)
                        custom_data[name] = loaded
                    except Exception as e:
                        self.handle_generic_exception(e, 'Error loading data')

            # template.render() returns a string which contains the rendered html
            language = language[0] if type(language) == list else 'en_US'
            html_output = template.render(
                data=custom_data,
                language=language,
                config=self.config,
            )

            return html_output

        except JINJA_GENERIC_EXCEPTION as e:
            return self.handle_jinja_generic_exception(e)
        except JINJA_DETAILED_EXCEPTION as e:
            return self.handle_jinja_detailed_exception(e)
        except Exception as e:
            return self.handle_generic_exception(e)


    def build(self):
        """
        take entire source directory and build to static HTML files
        """
        try:
            shutil.rmtree(self.build_path)
        except Exception as e:
            pass

        # check the config for languages and build away
        config = self.get_config()
        languages = config.get('languages', False)
        if languages:
            for language in languages:
                language_build_path = os.path.join(self.build_path, language)
                self.build_language(self.source_path, language_build_path, language)
        else:
            self.build_language(self.source_path, self.build_path)


    def build_language(self, source_path, build_path, language=False):
        """
        copy a source path and build it into a build
        """
        shutil.copytree(source_path, build_path)
        try:
            # re-write HTML as jinja2 HTML output
            for path, folders, files in os.walk(build_path):
                for file in files:
                    if file.endswith(tuple(self.config.get('template_extensions'))):
                        self.save_static_file(path, file, language=language)
        except Exception as e:
            self.handle_generic_exception(e, 'Build error')


    def save_static_file(self, path, file, **kwargs):
        """
        save the static file to build directory
        """
        try:
            file_path = os.path.join(path, file)
            language = kwargs.get('language', False)

            html = self.render_html(file_path, build=True, language=language)
            if html is None:
                raise Exception('Failed to render HTML. Response'
                                'from Prototype.render_html() is `None`.')

            f = open(path + '/' + file, 'w')
            f.write(html.encode('utf-8'))
            f.close()
        except Exception as e:
            self.handle_generic_exception(e, 'Generate static file error')

    def reload_hook(self):
        print 'Reload.'


    def get_config(self):
        return self.config

    def handle_jinja_generic_exception(self, e):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        error_renderer = ErrorRenderer()
        response = error_renderer.format_html_traceback(e, exc_tb)
        return response
        
    def handle_jinja_detailed_exception(self, e):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        error_renderer = ErrorRenderer()
        response = error_renderer.format_html_traceback(e, exc_tb)
        return response
        

    def handle_generic_exception(self, e, msg='Generic Exception'):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        error_renderer = ErrorRenderer()
        response = error_renderer.format_html_traceback(e, exc_tb)
        return response


class DefaultHandler(RequestHandler, Prototype):
    def get(self):
        try:
            uri = self.__dict__['request'].uri
            parsed = urlparse.urlparse(uri)
            path = parsed[2]
            if path == '/':
                path = '/index.html'
            self.write(self.render_html(path))
        except Exception as e:
            error_renderer = ErrorRenderer()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            response = error_renderer.format_html_traceback(e, exc_tb)
            self.write(response)

class TranslatedHandler(RequestHandler, Prototype):
    def get(self, language):
        try:
            uri = self.__dict__['request'].uri
            uri = uri.replace(language + '/', '')
            parsed = urlparse.urlparse(uri)
            path = parsed[2]
            if path == '/':
                path = '/index.html'
            self.write(self.render_html(path, language=language))
        except Exception as e:
            error_renderer = ErrorRenderer()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            response = error_renderer.format_html_traceback(e, exc_tb)
            self.write(response)

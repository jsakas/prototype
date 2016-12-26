from jinja2 import Environment, FileSystemLoader, TemplateNotFound

import traceback, os

class ErrorRenderer():
    def __init__(self):
        self.template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'html')
        template_loader = FileSystemLoader(searchpath=self.template_path)
        self.jinja_environment = Environment(
            loader=template_loader,
        )

    def format_html_traceback(self, e, tb):
        template_file = 'error.html'
        try:
            template = self.jinja_environment.get_template(template_file)
        except TemplateNotFound as e:
            print('Cannot locate template {} <br /><br />{}'.format(template_file, str(e)))
            return ''

        html_traceback = []
        for line in traceback.extract_tb(tb):
            entry =  'File {}, line {}, in {} <br />'.format(line[0], line[1], line[2])
            entry += '&nbsp;&nbsp;&nbsp;&nbsp;{}'.format(line[3])
            html_traceback.append(entry)

        html_output = template.render(
            error_name = type(e).__name__,
            title = str(e),
            html_traceback = html_traceback,
        )

        return html_output

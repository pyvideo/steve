#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012, 2013 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

# Things to know about this module. If you look at this code, you
# might be inclined to think, "wait--wtf is going on here?" I tried to
# do what I could to not add more library requirements, so there's a
# bunch of goofy stuff in here. I ended up using Jinja2 because I
# couldn't do it without either writing a templating system or losing
# my sanity.


import cgi
import urlparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from jinja2 import Environment, PackageLoader
from steve.util import (out, get_project_config, load_json_files,
                        save_json_file, get_video_requirements)


# http://blog.doughellmann.com/2007/12/pymotw-basehttpserver.html
# That helped a ton.


env = Environment(loader=PackageLoader('steve', 'templates'), autoescape=True)
HOST = 'localhost'
PORT = 8000


def get_data(cfg, fn):
    data_files = load_json_files(cfg)
    data_files = [d for d in data_files if d[0][5:] == fn]
    return data_files[0] if data_files else None


class WebEditRequestHandler(BaseHTTPRequestHandler):
    def parse_path(self):
        path = urlparse.urlparse(self.path).path.split('/')
        return [p for p in path if p]

    def parse_form(self):
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type'],
                     })
        return form

    def render_error(self, error_code):
        self.send_error(error_code)

    def redirect(self, location):
        self.send_response(303)
        self.send_header('Location', location)
        self.end_headers()

    def render_response(self, code, template, variables=None, headers=None):
        self.send_response(code)
        if headers:
            for key, val in headers:
                self.send_header(key, val)
        self.end_headers()
        if variables is None:
            variables = {}
        template = env.get_template(template)
        self.wfile.write(template.render(**variables).encode('utf-8'))

    def do_GET(self):
        path = self.parse_path()
        if not path:
            return self.route_home(path)

        if path[0] == 'edit':
            return self.route_edit(path)

        return self.render_error(404)

    def do_POST(self):
        path = self.parse_path()
        if path[0] == 'save':
            return self.route_save(path)
        return self.render_error(404)

    def route_home(self, path):
        config = get_project_config()
        self.render_response(200, 'home.html', {
                'title': config.get('project', 'category'),
                'data_files': load_json_files(config)
                })

    def route_edit(self, path):
        cfg = get_project_config()
        data_file = get_data(cfg, path[1])
        if not data_file:
            return self.render_error(404)

        fn, data = data_file
        reqs = get_video_requirements()

        # TODO: verify the data and add the errors to the fields?

        all_files = [filename for filename, _ in load_json_files(cfg)]
        fn_index = all_files.index(fn)
        prev_fn = all_files[fn_index - 1] if fn_index > 0 else ''
        next_fn = all_files[fn_index + 1] if fn_index < len(all_files) - 1 else ''

        fields = []

        category = cfg.get('project', 'category')

        for req in reqs:
            key = req['name']
            if key == 'category' and category:
                fields.append({
                        'name': req['name'],
                        'value': category
                        })
            else:
                fields.append({
                        'name': req['name'],
                        'type': req['type'],
                        'choices': req['choices'],
                        'html': req['html'],
                        'value': data.get(key, '')
                        })

        self.render_response(200, 'edit.html', {
                'title': 'edit %s' % data['title'],
                'fn': fn,
                'fields': fields,
                'prev_fn': prev_fn,
                'next_fn': next_fn
                })

    def route_save(self, path):
        cfg = get_project_config()
        data_file = get_data(cfg, path[1])
        if not data_file:
            return self.render_error(404)

        fn, data = data_file
        form_data = self.parse_form()
        reqs = get_video_requirements()

        for req in reqs:
            key = req['name']
            if key in form_data:
                value = None
                if req['type'] == 'IntegerField':
                    value = int(form_data[key].value)
                elif req['type'] == 'BooleanField':
                    value = bool(int(form_data[key].value))
                elif req['type'] in ('DateField', 'DateTimeField'):
                    # TODO: Verify the data format
                    value = form_data[key].value
                elif req['type'] in ('CharField', 'TextField'):
                    value = form_data[key].value
                elif req['type'] == 'SlugField':
                    # TODO: Verify the data format. Maybe if there is
                    # no slug field, we create it from the title?
                    value = form_data[key].value
                elif req['type'] in ('TextArrayField'):
                    # Split the field on carriage returns and drop any
                    # empty strings.
                    value = [mem.strip()
                             for mem in form_data[key].value.split('\n')
                             if mem.strip()]

                data[key] = value
            else:
                if req['type'] in ('CharField', 'TextField'):
                    data[key] = ''

                # TODO: What to do about other fields? Set to default?

        save_json_file(cfg, fn, data)

        return self.redirect('/edit/%s' % fn[5:])


def serve():
    httpd = HTTPServer((HOST, PORT), WebEditRequestHandler)
    out('Web edit system running on http://%s:%s/' % (HOST, PORT))
    out('ctrl-c to exit.')
    httpd.serve_forever()

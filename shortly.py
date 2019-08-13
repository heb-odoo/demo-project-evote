import os
import json
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
from jinja2 import Environment, FileSystemLoader
class Shortly(object):
    def __init__(self):
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)
        self.url_map = Map([
            Rule('/', endpoint='index_url'),
            Rule('/search_controller', endpoint='search_controller'),
            Rule('/like_update',endpoint='like_update')
        ])

    def index_url(self, request):
        with open('static/dataUrl.json') as response:
            source = response.read()
        data = json.loads(source)
        return self.render_template("app.html", data=data)

    def like_update(self, request):
        Mylikes = request.args.get('likes')
        Myid = request.args.get('id')

        print(Mylikes)              
        print(Myid)

        with open('static/dataUrl.json') as response:
            source = response.read()
        data = json.loads(source)
        updated_row = []
        for i in data["results"]:   
            if Myid in i['id']:
                if int(Mylikes) < 0:
                    i["dislike"] = Mylikes
                else:
                    i["like"] = Mylikes
                updated_row.append(i)
            
        jsonFile = open("static/dataUrl.json", "w+")
        jsonFile.write(json.dumps(data))
        print(data)
        jsonFile.close()

        return Response(json.dumps(updated_row), mimetype='application/json')


    def search_controller(self, request):
        filterdata = request.args.get('filter')
        with open('static/dataUrl.json') as response:
            source = response.read()
        data = json.loads(source)

        myFilterData = []

        for i in data["results"]:   
            if filterdata in i['Question']:
                myFilterData.append(i) 


        print(myFilterData)

        return Response(json.dumps(myFilterData), mimetype='application/json')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, endpoint)(request, **values)
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def render_template(self, templatename, **context):
        t = self.jinja_env.get_template(templatename)
        return Response(t.render(context), mimetype='text/html')

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def create_app():
    app = Shortly()
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/static':  os.path.join(os.path.dirname(__file__), 'static')
    })
    return app

if __name__ == '__main__':
        from werkzeug.serving import run_simple
        app = create_app()
        run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)
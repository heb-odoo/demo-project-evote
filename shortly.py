import os
import json
import secrets
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound, Forbidden
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
from jinja2 import Environment, FileSystemLoader

session = {}

class Shortly(object):
    def __init__(self):
        #self.sessions = ["sid":"1"]
        #response.set_cookie('cookie_name', request.sessions.sid)

        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)
        self.url_map = Map([
            Rule('/', endpoint='index_url'),
            Rule('/search_controller', endpoint='search_controller'),
            Rule('/like_update',endpoint='like_update')
        ])

    def index_url(self, request):
        global session
        token = request.cookies.get('session_id')
        if token is None:
            token = self.make_token()
            session.update({
                'session_id': token,
                'totalLikes': 0,
                'totalDisLikes': 0,
                })

        # value = { 'session_id': token }

        # if 'totalLikes' not in session.keys():
        #     value.update({
        #         'totalLikes': 0
        #         })
        # if 'totalDisLikes' not in session.keys():
        #     value.update({
        #         'totalDisLikes': 0
        #         })
        # session.update(value)

        if token != session.get('session_id'):
            raise Forbidden()

        print(session)
        with open('static/dataUrl.json') as response:
            source = response.read()

        # print('=============> data')
        # print(source, type((source)))
        data = json.loads(source)
        # print(data, type((data)))
        data.update({
            'totalLikes': session.get('totalLikes'),
            'totalDisLikes': session.get('totalDisLikes')
            })

        print('========> data', data)

        response = self.render_template("app.html", data=data)
        response.set_cookie('session_id',token)

        return response


    def like_update(self, request):
        global session
        Mylikes = request.args.get('likes')
        Myid = request.args.get('id')

        print(Mylikes)              
        print(Myid)

        totalLikes = session.get('totalLikes')
        totalDisLikes = session.get('totalDisLikes')

        with open('static/dataUrl.json') as response:
            source = response.read()
        data = json.loads(source)
        updated_row = []
        for i in data["results"]:   
            if Myid in i['id']:
                if int(Mylikes) < 0:
                    i["dislike"] = Mylikes
                    totalDisLikes+=1
                else:
                    i["like"] = Mylikes
                    totalLikes+=1
                updated_row.append(i)

        session.update({
            'totalLikes': totalLikes,
            'totalDisLikes': totalDisLikes
            })

        result = { "row": updated_row , "totalLikes" : totalLikes , "totalDisLikes" : totalDisLikes}
        # print(json.dumps(result))

        jsonFile = open("static/dataUrl.json", "w+")
        jsonFile.write(json.dumps(data))
        # print(data)
        # print(updated_row)
        jsonFile.close()

        return Response(json.dumps(result), mimetype='application/json')
        


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


    def make_token(self):
        return secrets.token_urlsafe(16)

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
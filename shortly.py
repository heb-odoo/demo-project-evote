import os
import json
import secrets
import csv
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound, Forbidden
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
from jinja2 import Environment, FileSystemLoader

# session = {}

class Shortly(object):
    def __init__(self):
        #self.sessions = ["sid":"1"]
        #response.set_cookie('cookie_name', request.sessions.sid)
        self.session = {}

        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)
        self.url_map = Map([
            Rule('/', endpoint='index_url'),
            Rule('/search_controller', endpoint='search_controller'),
            Rule('/like_update',endpoint='like_update')
        ])

    def index_url(self, request):
        session_id = request.cookies.get('session_id')
        print('==========>session',session_id)
   
        if not session_id:
            session_id = self.make_token()
            self.session = self.create_session(session_id)
        else:
            self.session = self.read_session(session_id)

        with open('static/dataUrl.json') as response:
            source = response.read()

        data = json.loads(source)
        response = self.render_template("app.html", data=data, session_data=self.session)
        response.set_cookie('session_id',self.session['session_id'])

        return response


    def like_update(self, request):
        # global session
        Mylikes = request.args.get('likes')
        Myid = request.args.get('id')
        # import pdb ; pdb.set_trace()

        with open('static/dataUrl.json') as response:
            source = response.read()
        data = json.loads(source)
        updated_row = []
        for i in data["results"]:   
            if Myid in i['id']:
                if int(Mylikes) < 0:
                    i["dislike"] = Mylikes
                    self.session['totalDisLikes'] += 1

                else:
                    i["like"] = Mylikes
                    self.session['totalLikes'] += 1
                updated_row.append(i)



        result = { "row": updated_row}
        print(self.session)


        jsonFile = open("static/dataUrl.json", "w+")
        jsonFile.write(json.dumps(data))

        jsonFile.close()
        with open('static/session.json') as response:
            session_source = response.read()
        session_data = json.loads(session_source)
        newData = []
        for session in session_data["session_data"]:   
            if self.session['session_id'] in session['session_id']:
                session = self.session
            newData.append(session)

        sessionFile = open("static/session.json", "w+")
        sessionData = {'session_data': newData}
        sessionFile.write(json.dumps(sessionData))

        sessionFile.close()

        response = {
            "updated_row":updated_row,
            "session": self.session 
        }
        return Response(json.dumps(response), mimetype='application/json')
        


    def search_controller(self, request):
        filterdata = request.args.get('filter')
        with open('static/dataUrl.json') as response:
            source = response.read()
        data = json.loads(source)

        myFilterData = []

        for i in data["results"]:   
            if filterdata in i['Question']:
                myFilterData.append(i) 

        return Response(json.dumps(myFilterData), mimetype='application/json')


    def make_token(self):
        return secrets.token_urlsafe(16)

    def read_session(self, session_id):
        with open('static/session.json') as response:
            source = response.read()
        data = json.loads(source)

        for session in data["session_data"]:   
            if session_id in session['session_id']:
                return session

    def create_session(self, session_id):
        with open('static/session.json') as response:
            data = response.read()
        session_data = json.loads(data)
        data = { "session_id": session_id , "totalLikes" : 0 , "totalDisLikes" : 0}
        session_data['session_data'].append(data)     
        jsonFile = open("static/session.json", "w")
        jsonFile.write(json.dumps(session_data))
        jsonFile.write("\n")
        jsonFile.close()
        return data


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
# The master handles user authentication and passes user to data server.
# potentially add: the ability to allow user to choose to host or listen...


import jinja2
import os
import logging
from django.utils import simplejson

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from dataServer import *

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        session_key = self.request.get('session_key')
        session = None

        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return

        if not session_key:
            # No session specified, create a new one, make this the host 
            session_key = user.user_id()
            session = Session(key_name = session_key,   # Key for the db.Model. 
                              host = user,
                              curSongIdx = 0,
                              play = False,
                              eFlag = False)
            session.put()
        else:
            # Session exists 
            session = Session.get_by_key_name(session_key)
            listeners = Session.get(session.listeners)
            if not session.host and (user not in listeners):
                # User not in listener list 
                listeners.append(user)
                session.put()

        session_link = 'http://localhost:8080/?session_key=' + session_key

        if session:
            token = channel.create_channel(user.user_id() + session_key)
            template_values = {'token': token,
                               'me': user.user_id(),
                               'session_key': session_key,
                               'session_link': session_link,
                               'initial_message': SessionUpdater(session).get_session_message()
                               }
            template = jinja_environment.get_template('index.html')
            self.response.out.write(template.render(template_values))
        else:
            self.response.out.write('No existing session')

class TestPage(webapp.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render({}))
        
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
app = webapp.WSGIApplication(
    [('/', MainPage),
     ('/open', OpenPage),
     ('/update', UpdateChannel),
     ('/remove', RemoveListener),
     ('/generate_upload_url', UploadURL),
     ('/upload', UploadSong),
	 ('/sessions', GetLiveSessions),
     ('/serve/([^/]+)?', ServeSong),
     ('/test', TestPage)], debug=True)

def main():
    run_wsgi_app(app)

if __name__ == "__main__":
    main()


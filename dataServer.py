import jinja2
import os
import logging
from django.utils import simplejson

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

    
###############################################################
# Session classes and structures

# TODO: figure out why put is failing
# RequestTooLargeError: The request to API call datastore_v3.Put() was too large.

# Stored data for session
# Identified by session_key = user.user_id() of host user
class Session(db.Model):
    host = db.UserProperty()        # Host user
#    listener = db.UserProperty()    # Listener user
    listeners = db.ListProperty(users.User)    # List of listeners
    song = db.StringProperty()      # Song data
    data = db.BlobProperty()        # Data 
    eFlag = db.BooleanProperty()    # End flag
    
class SessionUpdater():
    session = None
    def __init__(self, session):
        self.session = session
    
    # receive update to session
    def get_session_message(self):
        sessionUpdate = {
            'song': self.session.song,
            'host': self.session.host.user_id(),
            'listeners': self.session.listeners,
            # TODO: we need to send the url for the song data
            #'data': self.session.data,
            'endFlag': self.session.eFlag
        }
        return simplejson.dumps(sessionUpdate)
    
    # Update channel clients
    def send_update(self):
        message = self.get_session_message()
        channel.send_message(self.session.host.user_id() + self.session.key().id_or_name(), message)
        logging.info('send_update: ' + str(message))
        # EXTEND: Update all listeners
        for lst in Session.get(self.session.listeners):
            channel.send_message(lst.user_id() + self.session.key().id_or_name(), message)
    
    # Song stuff
    def update_song(self, song, data, eFlag):
        # send data
        self.session.song = song
        self.session.data = data
        self.session.eFlag = eFlag
        self.session.put()
        self.send_update()
        
class SessionFromRequest():
    session = None;
    def __init__(self, request):
        user = users.get_current_user()
        session_key = request.get('session_key')
        logging.info('SessionFromRequest session_key:' + str(session_key))
        if user and session_key:
            self.session = Session.get_by_key_name(session_key)
    
    def get_session(self):
        return self.session

#########################################
# Handler code

# Make updates to session
class UpdateSong(webapp.RequestHandler):
    def post(self):
        session = SessionFromRequest(self.request).get_session()
        user = users.get_current_user()
        if session and user:
            song = self.request.get('song')
            data = self.request.get('data')
            endFlag = self.request.get('endflag')
            
            if not endFlag:
                endFlag = False
            
            SessionUpdater(session).update_song(song, data, endFlag)

# Request to update the page
class OpenPage(webapp.RequestHandler):
    def post(self):
        session = SessionFromRequest(self.request).get_session()
        SessionUpdater(session).send_update()

class TestPage(webapp.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render({}))


################# MOVED TO masterServer.py ######################################
# class MainPage(webapp.RequestHandler):
#     def get(self):
#         user = users.get_current_user()
#         session_key = self.request.get('session_key')
#         session = None
        
#         if not user:
#             self.redirect(users.create_login_url(self.request.uri))
#             return
        
#         if not session_key:
#             # No session specified, create a new one, make this the host
#             session_key = user.user_id()
#             session = Session(key_name = session_key,   # Key for the db.Model.
#                               host = user,
#                               eFlag = False)    
#             session.put()
#         else:
#             # Session exists
#             session = Session.get_by_key_name(session_key)
#             listeners = Session.get(session.listeners)
#             if not session.host and (user not in listeners):
#                 # User not in listener list
#                 listeners.append(user)
#                 session.put()
        
#         session_link = 'http://localhost:8080/?session_key=' + session_key
        
#         if session:
#             token = channel.create_channel(user.user_id() + session_key)
#             template_values = {'token': token, 
#                                'me': user.user_id(),
#                                'session_key': session_key,
#                                'session_link': session_link,
#                                'initial_message': SessionUpdater(session).get_session_message()
#                                }
#             template = jinja_environment.get_template('index.html')
#             self.response.out.write(template.render(template_values))
#         else:
#             self.response.out.write('No existing session')

        
# jinja_environment = jinja2.Environment(
#     loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
# app = webapp.WSGIApplication(
#     [('/', MainPage),
#      ('/open', OpenPage),
#      ('/update', UpdateSong),
#      ('/test', TestPage)], 
#     debug=True)

# def main():
#     run_wsgi_app(app)
    
# if __name__ == "__main__":
#     main()

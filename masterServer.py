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

def ACL_key(user_name=None):
    """ Constructs a key from """
    return db.Key.from_path('ACL', user_name or 'anonymous')

def findACL(user):
    return db.get(ACL_key(user.user_id()))


class LoggedInUsers(db.Model):
    """
    Create reverse mapping from emails to user ids
    (emails are the keys)
    """
    userid = db.StringProperty()

class ACLEntry(db.Model):
    """
    Individual ACL (Access Control List) entry. 
    Keeps track for each user who can listen to their sessions (potential listeners) 
    and which sessions the user can listen to (potential sessions) 
    """
    host       = db.UserProperty()                              # User 
    plisteners = db.ListProperty(users.User, indexed=False)     # List of users who are allowed to listen to this one 
    psessions  = db.ListProperty(users.User, indexed=False)     # List of users whose session this user can listen to


    def add(self, host, plistener):
        """ Adds plistener to host's plistener ACL 
        and adds host to plistener's psessions ACL.
        For performance, allows duplicates."""

        host_entry = db.get(ACL_key(host.user_id()))
        host_entry.plisteners.append(plistener)
        host_entry.put()

        plistener_entry = db.get(ACL_key(plistener.user_id()))
        plistener_entry.psessions.append(host)
        plistener_entry.put()

    def remove(self, host, plistener):
        """ Removes plistener to host's plistener ACL 
        and removes host to plistener's psessions ACL.
        Accounts for duplicates. """

        # TODO: don't put if no change?
        host_entry = db.get(ACL_key(host.user_id()))
        while (plistener in host_entry.plisteners):
            host_entry.plisteners.remove(plistener.user_id())
        host_entry.put()

        plistener_entry = db.get(ACL_key(plistener.user_id()))
        while (host in plistener_entry.psessions):
            plistener_entry.psessions.append(host)
        plistener_entry.put()


class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        session_key = self.request.get('session_key')
        session = None

        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return

        ACL = findACL(user)
        # if user has no ACL, create one with no listeners and no potential sessions
        if (ACL == None):
            ACL = ACLEntry(host = user,
                           plisteners = [],
                           psessions = [])
            ACL.put()

        # ADD USER TO LIST OF LOGGED IN USERS
        # (so other users can add to listner list
        addlog = LoggedInUsers(key_name = user.email(),
                              userid = user.user_id())
        addlog.put()

            
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
                               }
            # combine these so that they can be used on the client side
            template_values.update(SessionUpdater(session).get_session_details())

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


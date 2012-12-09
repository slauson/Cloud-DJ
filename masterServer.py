# The master handles user authentication and passes user to data server.
# potentially add: the ability to allow user to choose to host or listen...
import jinja2
import os
import logging
import random
from django.utils import simplejson

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import string

from dataServer import *

# TODO: fix keys to be more standard?

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
    host       = db.UserProperty()                       # User 
    sessionkey = db.StringProperty()                     # user's session key - server can recreate channel ID
    plisteners = db.ListProperty(str, indexed=False)     # List of users who are allowed to listen to this one 
    psessions  = db.ListProperty(str, indexed=False)     # List of users whose session this user can listen to


class ACLHandler():
    def add(self, host, plistener):
        """ Adds plistener to host's plistener ACL 
        and adds host to plistener's psessions ACL.
        For performance, allows duplicates."""

        host_entry = findACL(host)
        host_entry.plisteners.append(plistener)
        host_entry.put()

        plistener_entry = findACL(plistener)
        plistener_entry.psessions.append(host)
        plistener_entry.put()

    def remove(self, host, plistener):
        """ Removes plistener to host's plistener ACL 
        and removes host to plistener's psessions ACL.
        Accounts for duplicates. """

        # TODO: don't put if no change?
        host_entry = findACL(host)
        while (plistener in host_entry.plisteners):
            host_entry.plisteners.remove(plistener.user_id())
        host_entry.put()

        plistener_entry = findACL(plistener)
        while (host in plistener_entry.psessions):
            plistener_entry.psessions.append(host)
        plistener_entry.put()


class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        session_key = str(self.request.get('session_key'))
        session = None

        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return

        if not session_key:
            # No session specified, create a new one, make this the host 
            # session_key = user.user_id()
            session_key = session_key_gen()
            curTime = datetime.now()
            session = Session(key_name = session_key,   # Key for the db.Model. 
                              host = user,
                              curSongIdx = 0,
                              play = False,
                              eFlag = False,
                              timestamp = curTime)
            session.put()
        else:
            # Session exists 
            session = Session.get_by_key_name(session_key)

            if not session:
                self.response.out.write('Invalid session ' + session_key)
                return

            listeners = session.listeners
            if not session.host and (user not in listeners):
                # User not in listener list 
                listeners.append(user)
                session.put()
                SessionUpdater(session).send_update(SessionUpdater(session).get_session_message())

        ACL = findACL(user.user_id())
        # if user has no ACL, create one with no listeners and no potential sessions
        if (ACL == None):
            ACL = ACLEntry(key_name=user.user_id(),
                           host = user,
                           sessionkey = session_key, 
                           plisteners = [],
                           psessions = [])
            ACL.put()

        # TODO: remove when user logs out
        # ADD USER TO LIST OF LOGGED IN USERS
        # (so other users can add to listner list
        addlog = LoggedInUsers(key_name = user.email(),
                              userid = user.user_id())
        addlog.put()


        session_link = 'http://localhost:8080/?session_key=' + session_key
        logout_link = users.create_logout_url('/')

        if session:
            token = channel.create_channel(user.user_id() + "_" + session_key)
            template_values = {'token': token,
                               'me': user.user_id(),
							   'me_email': user.email(),
                               'session_key': session_key,
                               'session_link': session_link,
                               'logout_link': logout_link,
                               }
            # combine these so that they can be used on the client side
            #template_values.update(SessionUpdater(session).get_session_details())

            template = jinja_environment.get_template('index.html')
            self.response.out.write(template.render(template_values))
        else:
            self.response.out.write('No existing session')


class AddListener(webapp.RequestHandler):
    """
    Add (potential) listener to user's ACL list.
    
    Client submits e-mail of person to add and 
    if that user is online, server can add to ACL
    """
    def post(self):
        user = users.get_current_user() # user making request
        email = self.request.get('email') #email of potential listner to add

        # see if user is online
        userid = ACLEntry.get_by_key_name(email)
        if (userid != None):
            # they're online and can be added
            ACLHandler().add(user.user_id, userid)

class RemoveListener(webapp.RequestHandler):
    """
    """
    def post(self):
        user = users.get_current_user() # user making request
        email = self.request.get('email') #email of potential listner to add

        # see if user is online
        if (email != ''): # ignore blank emails
            userid = db.get(email)
            if (userid != None):
                # they're online and may be in this users list
                ACLHandler().remove(user.user_id, userid)
# FOR TESTING ONLY:
#         userid = db.get(email)
#         if (userid != None):
#             # they're online and may be in this users list
#             ACLHandler().remove(user.user_id, userid)
        

class TestPage(webapp.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render({}))
        
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
app = webapp.WSGIApplication(
    [('/', MainPage),
     ('/open', OpenPage),
     ('/logout', Logout),
     ('/_ah/channel/disconnected', ChannelDisconnect),
     ('/update', UpdateChannel),
     ('/info', SessionInfo),
     ('/remove', RemoveListener),
     ('/generate_upload_url', UploadURL),
     ('/upload', UploadSong),
     ('/add_listener', AddListener),
     ('/sessions', GetLiveSessions),
     ('/serve/([^/]+)?', ServeSong),
     ('/test', TestPage)], debug=True)

def session_key_gen():
    chars=string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for x in range(10))


def main():
    run_wsgi_app(app)
    
if __name__ == "__main__":
    main()


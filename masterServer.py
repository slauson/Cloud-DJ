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
    db.get(ACL(key(user.userid()))
#     db.GqlQuery("SELECT * "
#                 "FROM "
#                 "WHERE ANCESTOR IS :1", 
#                 ACL_key(user.user_id()))
    # Comment: 
    # Ancestor queries, as shown here, are strongly consistent; queries that
    # span entity groups are only eventually consistent. If we omitted the
    # ancestor from this query, there would be a slight chance that a greeting
    # that had just been written would not show up in a query. See example:
    #     greetings = db.GqlQuery("SELECT * "
    #                             "FROM Greeting "
    #                             "WHERE ANCESTOR IS :1 "
    #                             "ORDER BY date DESC LIMIT 10",
    #                             guestbook_key(guestbook_name))


class ACLEntry(db.Model):
    """
    Individual ACL (Access Control List) entry. 
    Keeps track for each user who can listen to their sessions (potential listeners) 
    and which sessions the user can listen to (potential sessions) 
    """
    host       = db.UserProperty()                              # User 
    plisteners = db.ListProperty(users.User, indexed=False)     # List of users who are allowed to listen to this one 
    psessions  = db.ListProperty(users.User, indexed=False)     # List of users whose session this user can listen to


    def create_new(self, user):
        host = user
        plisteners = []
        psessions = []

    def put(self):
        self.put()

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
        
#         ACL = findACL(user)
#         if (ACL == None):
#             ACL = ACLEntry()
#             ACL.create_new()
#             ACL.put()

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
     ('/serve/([^/]+)?', ServeSong),
     ('/test', TestPage)], debug=True)

def main():
    run_wsgi_app(app)

if __name__ == "__main__":
    main()


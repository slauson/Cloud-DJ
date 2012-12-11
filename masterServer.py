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
from google.appengine.api import app_identity 

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

class ACLHandler():
    def add(self, host, plistener):
        """ Adds plistener to host's plistener ACL 
        and adds host to plistener's psessions ACL.
        For performance, allows duplicates."""

        host_entry = findACL(host)
        if (host_entry.plisteners != None):
            host_entry.plisteners.append(str(plistener))
        else:
            host_entry.plisteners = [str(plistener)]
        host_entry.put()

        plistener_entry = findACL(plistener)
        if (plistener_entry.psessions != None):
            plistener_entry.psessions.append(str(host))
        else:
            plistener_entry.psessions = [str(host)]
        plistener_entry.put()

    def remove(self, host, plistener):
        """ Removes plistener to host's plistener ACL 
        and removes host to plistener's psessions ACL.
        Accounts for duplicates. """

        host_entry = findACL(host)
        if (host_entry.plisteners != None):
            while (plistener in host_entry.plisteners):
                host_entry.plisteners.remove(plistener.user_id())
            host_entry.put()

        plistener_entry = findACL(plistener)
        if (plistener_entry.psessions != None):
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
            # If this user is already hosting, connect them to the existing session
            q = Session.all().filter("host =", user)
            session = q.get()
            if not session:
                session_key = session_key_gen()
                curTime = datetime.datetime.now()
                session = Session(key_name = session_key,   # Key for the db.Model. 
                                  host = user,
                                  curSongIdx = 0,
                                  play = False,
                                  endFlag = False,
                                  timestamp = curTime)
                session.put()
            else:
                session_key = session.key().name()
        else:
            # Session exists 
            session = Session.get_by_key_name(session_key)

            if not session:
                self.response.out.write('Invalid session ' + session_key)
                return

            logging.info('existing session: ' + str(user) + ', ' + str(session.host))
            if user != session.host and (user not in session.listeners):
                logging.info('add user ' + str(user.email()) + ' to listeners')
                # User not in listener list 
                session.listeners.append(user)
                session.put()
                SessionUpdater(session).send_update(SessionUpdater(session).get_session_message())

            # Perform cleanup where we remove any sessions for which we are the host
            q = Session.all().filter('host =', user)
            for ses in q.run(read_policy=db.STRONG_CONSISTENCY):
                SessionUpdater(ses).remove_session()

        ACL = findACL(user.user_id())
        # if user has no ACL, create one with no listeners and no potential sessions
        if (ACL == None):
            ACL = ACLEntry(key_name=str(user.user_id()),
                           host = user,
                           sessionkey = session_key, 
                           plisteners = [],
                           psessions = [])
            ACL.put()

        # TODO: remove when user logs out
        # ADD USER TO LIST OF LOGGED IN USERS
        # (so other users can add to listner list)
        addlog = LoggedInUsers(key_name = user.email(),
                               userid = user.user_id())
        addlog.put()


        # Deployed version:
        session_link = 'http://2.' + app_identity.get_default_version_hostname() + '/?session_key=' + session_key
        #session_link = 'http://localhost:8080/?session_key=' + session_key
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
            
            # send update out when someone joins session
            #SessionUpdater(session).send_update(SessionUpdater(session).get_session_message())

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
        if (email != ''): #ignore blank emails
            Otherloggedinuser = LoggedInUsers.get_by_key_name(email)
            listener_userid = Otherloggedinuser.userid
            if (listener_userid != None):
                # they're online and can be added
                ACLHandler().add(user.user_id(), listener_userid)

                # UPDATE NEW LISTENER'S CHANNEL
                
                # first check if user is actually a host, not a listener
                hostACL = findACL(user.user_id())
                session = Session.get_by_key_name(hostACL.sessionkey)
                if (session.host.user_id() == user.user_id()):
                    # actually a host
                    # send info on new listener's channel
                    # TODO: does this channel even exist?
                    #message = SessionUpdater(session).get_session_message()
                    #logging.info('send_message to ' + str(listener_userid + '_' + hostACL.sessionkey + ': ' + str(message)))
                    #channel.send_message(listener_userid + '_' + self.session.key().id_or_name(), message)
                    # TODO: send incremental update instead of entire thing list of everything



class RemoveListener(webapp.RequestHandler):
    """
    """
    def post(self):
        user = users.get_current_user() # user making request
        email = self.request.get('email') #email of potential listner to add

        # see if user is online
        if (email != ''): # ignore blank emails
            Otherloggedinuser = LoggedInUsers.get_by_key_name(email)
            userid = Otherloggedinuser.userid
            if (userid != None):
                # they're online and may be in this users list
                ACLHandler().remove(user.user_id(), userid)
        

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
     ('/serve/([^/]+)?', ServeSong)], debug=True)

def session_key_gen():
    chars=string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for x in range(10))


def main():
    run_wsgi_app(app)
    
if __name__ == "__main__":
    main()


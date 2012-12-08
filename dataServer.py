import jinja2
import os
import urllib

from django.utils import simplejson

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext import blobstore
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import blobstore_handlers

    
###############################################################
# Session classes and structures    

class Song(db.Model):
    blob_key = blobstore.BlobReferenceProperty()
    artist = db.StringProperty()    # Metadata
    title = db.StringProperty()     # Metadata
    
# Stored data for session
# Identified by session_key = user.user_id()+session_key of host user
class Session(db.Model):
    host = db.UserProperty()# Host user
    listeners = db.ListProperty(users.User)         # List of listeners
    plisteners = db.ListProperty(users.User)
    curSongIdx = db.IntegerProperty()               # Index of current song in playlist...
    playlist = db.ListProperty(db.Key)              # Keys for songs
    play = db.BooleanProperty()                     # Play or not?
    endFlag = db.BooleanProperty()                  # End flag
        
class SessionUpdater():
    session = None
    def __init__(self, session):
        self.session = session
    
    # Update channel clients with the specified message
    def send_update(self, message):
        #message = self.get_session_message()
        channel.send_message(self.session.host.user_id() + self.session.key().id_or_name(), message)
        
        for lst in self.session.listeners:
            channel.send_message(lst.user_id() + self.session.key().id_or_name(), message)
            
    # Update message for non-incremental updates
    # Returns entire model  
    def get_session_message(self):
        playlist = self.session.playlist
        idx = self.session.curSongIdx
        song = Song.get(playlist[idx])
        sessionUpdate = {
            'host': self.session.host.user_id(),
            'listeners': self.session.listeners,
            'title': song.title,                    # Current song title
            'artist': song.artist,                  # Current song artist
            'curSongKey': str(song.blob_key),       # Current song blob key. Serve url: /serve/blob_key
            'play': self.session.play,              # Tell the client to play or not
            'endFlag': self.session.endFlag         # Session end or not
        }
        return simplejson.dumps(sessionUpdate)
    
    # Update song information only
    def get_song_message(self):
        playlist = self.session.playlist
        idx = self.session.curSongIdx
        song = Song.get(playlist[idx])
        sessionUpdate = {
            'title': song.title,
            'artist': song.artist,
            'curSongKey': str(song.blob_key),
            'play': self.session.play,
            'endFlag': self.session.endFlag
        }
        return simplejson.dumps(sessionUpdate)
    
    ##############
    # Updating the datastore model
    
    # Song stuff
    # Update song, play, endFlag
    # idx = index into playlist, play = bool, endFlag = bool
    def update_song(self, idx, play, endFlag):
        self.session.curIdx = idx
        self.session.play = play
        self.session.endFlag = endFlag
        self.session.put()    
        self.send_update(self.get_song_message())
        
        
    # Remove listener from listener list
    def remove_listener(self, user):
        self.session.listeners.remove(user)
        self.session.put()
        sessionUpdate = {
            'listeners': self.session.listeners
        }
        message = simplejson.dumps(sessionUpdate)
        self.send_update(message)
        
    # Add song to playlist
    def add_song(self, title_, artist_, blob_key_):
        song = Song(blob_key = blob_key_,
                    title = title_,
                    artist = artist_)
        song.put()
        self.session.playlist.append(song.key())
        self.session.put()
            
class SessionFromRequest():
    session = None;
    def __init__(self, request):
        user = users.get_current_user()
        session_key = request.get('session_key')
        if user and session_key:
            self.session = Session.get_by_key_name(session_key)
    
    def get_session(self):
        return self.session

#########################################
# Handler code

###########################################
# Session related handlers

# Make updates to session information
# Message from host
# Control the current song, play or pause, end session
# /update
class UpdateChannel(webapp.RequestHandler):
    def post(self):
        session = SessionFromRequest(self.request).get_session()
        user = users.get_current_user()
        if session and user == session.host:
            curIdx = self.request.get('curIdx')   # Index of the current song
            if (curIdx >= len(session.playlist)):
                break
            play = self.request.get('play')
            endFlag = self.request.get('endflag')
            SessionUpdater(session).update_song(curIdx, play, endFlag)

# Remove self from listeners
# /remove
class RemoveListener(webapp.RequestHandler):
    def post(self):
            session = SessionFromRequest(self.request).get_session()
            user = users.get_current_user()
            if session and user:
                SessionUpdater(session).remove_listener(user)
                
# Get all live sessions
# /sessions    
class GetLiveSessions(webapp.RequestHandler):
    def get(self):
            session = SessionFromRequest(self.request).get_session()
#           user = users.get_current_user()
            if session:
                sessionList = Session.all().filter('endFlag =', False)
                msg = ""
                for ses in sessionList:
                    song = Song.get(ses.playlist[ses.curIdx])
                    msg += ses.host + "," + song.title +"," + song.artist +"\n"
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write(msg)

##########################################
# Blob related handlers

# Generate unique upload URL for each file!!!!!
# Returns a text response with the upload url in the body
# /generate_upload_url
class UploadURL(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(blobstore.create_upload_url('/upload'))

# Upload a song. Javascript client will provide title and artist
# /upload
class UploadSong(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        session = SessionFromRequest(self.request).get_session()
        title = self.get('title')
        artist = self.get('artist')
        if (session.host == users.get_current_user()):
            upload_files = self.get_uploads('file')
            blob_info = upload_files[0]
            # add the song to datastore
            SessionUpdater(session).add_song(blob_info.key(), title, artist)
        
     
# Serve a song only if the session is valid and if play mode is on
# /serve/___   
class ServeSong(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        session = SessionFromRequest(self.request).get_session()
        blob_key = str(urllib.unquote(blob_key))
        if (session.eFlag and session.play and (str(session.curSong) == blob_key)):
            self.send_blob(blobstore.BlobInfo.get(blob_key))

# Request to open the page /open
class OpenPage(webapp.RequestHandler):
    def post(self):
        session = SessionFromRequest(self.request).get_session()
        SessionUpdater(session).send_update()

# Main page /
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
                              endFlag = False)    
            session.put()
        else:
            # Session exists
            session = Session.get_by_key_name(session_key)
            listeners = Session.get(session.listeners)
            if not session.host and (user not in listeners):
                # User not in listener list
                listeners.append(user)
                session.put()
        
        # Change this to be our app's link.
        session_link = 'http://localhost:8080/?session_key=' + session_key
        
        if session:
            token = channel.create_channel(user.user_id() + session_key)
            # Initial message for when the channel is open on the client
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

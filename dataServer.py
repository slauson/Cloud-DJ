import urllib
import logging
from django.utils import simplejson

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

    
###############################################################
# Session classes and structures 
   
class Song(db.Model):
    blob_key = blobstore.BlobReferenceProperty()
#    artist = db.StringProperty()    # Metadata
#    title = db.StringProperty()     # Metadata
    
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
        if not message:
            return
        channel.send_message(self.session.host.user_id() + self.session.key().id_or_name(), message)
        
        for lst in self.session.listeners:
            channel.send_message(lst.user_id() + self.session.key().id_or_name(), message)
            
    # Update message for non-incremental updates
    # Returns entire model  
    def get_session_message(self):
        playlist = self.session.playlist
        idx = self.session.curSongIdx
        sessionUpdate = {
            'host': self.session.host.user_id(),
            'listeners': self.session.listeners,
            'play': self.session.play,              # Tell the client to play or not
            'endFlag': self.session.endFlag         # Session end or not
        }
        if playlist and idx:
            song = Song.get(playlist[idx])
#            sessionUpdate['title']= song.title                  # Current song title
#            sessionUpdate['artist']= song.artist                 # Current song artist
            sessionUpdate['curSongKey']= str(song.blob_key)        # Current song blob key. Serve url: /serve/blob_key

        logging.info('get_session_message: ' + str(sessionUpdate))
        return simplejson.dumps(sessionUpdate)
    
    
    # Update song information only
    def get_song_message(self):
        playlist = self.session.playlist
        idx = self.session.curSongIdx
        
        if not playlist or not idx:
            return
        
        song = Song.get(playlist[idx])
        sessionUpdate = {
#            'title': song.title,
#            'artist': song.artist,
            'curSongKey': str(song.blob_key),
            'play': self.session.play,
            'endFlag': self.session.endFlag
        }
        return simplejson.dumps(sessionUpdate)
    
    # Send the most recently added blob key
    def get_blob_message(self, blob_key):
        sessionUpdate = {
            'newSongKey': str(blob_key)
        }
        return simplejson.dumps(sessionUpdate)
    ##############
    # Updating the datastore model
    
    # Song stuff
    # Update song, play, endFlag
    # idx = index into playlist, play = bool, endFlag = bool
    def update_song(self, idx, play, endFlag):
        self.session.curSongIdx = idx
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
    def add_song(self, blob_key_):
        song = Song(blob_key = blob_key_)
        song.put()
        self.session.playlist.append(song.key())
        self.session.put()
            
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
            if (curIdx < len(session.playlist)):
                play = self.request.get('play')
                endFlag = self.request.get('endflag')
                if not endFlag:
                    endFlag = False
                if not play:
                    play = True
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
                    song = Song.get(ses.playlist[ses.curSongIdx])
                    msg += ses.host + "," + str(song.blob_key) + "\n"
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
#        title = self.request.get('title')
#        artist = self.request.get('artist')
        if (session.host == users.get_current_user()):
            upload_files = self.get_uploads('file')
            blob_info = upload_files[0]
            # add the song to datastore
            SessionUpdater(session).add_song(blob_info.key())
            # Send message to everyone in the channel with the new blob key
            SessionUpdater(session).send_update(SessionUpdater(session).get_blob_message(blob_info.key()))
        
     
# Serve a song only if the session is valid and if play mode is on
# /serve/___   
class ServeSong(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        session = SessionFromRequest(self.request).get_session()
        blob_key = str(urllib.unquote(blob_key))
        
        playlist = session.playlist
        idx = session.curSongIdx
        song = Song.get(playlist[idx])
        if (session.endFlag and session.play and (str(song.blob_key) == blob_key)):
            self.send_blob(blobstore.BlobInfo.get(blob_key))

# Request to open the page /open
class OpenPage(webapp.RequestHandler):
    def post(self):
        session = SessionFromRequest(self.request).get_session()
        SessionUpdater(session).send_update(SessionUpdater(session).get_session_message())
        

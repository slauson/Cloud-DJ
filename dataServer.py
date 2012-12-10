import urllib
import logging
import time

from django.utils import simplejson
from datetime import datetime

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

##############################################################
#
def ACL_key(user_id):
    """ Constructs a key from the user id"""
    return db.Key.from_path('ACL', user_id)

def findACL(userid):
    return db.get(ACL_key(userid))

    
###############################################################
# Session classes and structures 
   
class Song(db.Model):
    blob_key = blobstore.BlobReferenceProperty()
    filename = db.StringProperty()    # Metadata
#    artist = db.StringProperty()    # Metadata
#    title = db.StringProperty()     # Metadata
    
# Stored data for session
# Identified by session_key = user.user_id()+session_key of host user
class Session(db.Model):
    host = db.UserProperty()# Host user
    listeners = db.ListProperty(users.User)         # List of listeners
    curSongIdx = db.IntegerProperty()               # Index of current song in playlist...
    playlist = db.ListProperty(db.Key,indexed=False)              # Keys for songs
    play = db.BooleanProperty()                     # Play or not?
    endFlag = db.BooleanProperty()                  # End flag
    timestamp = db.DateTimeProperty()                   # Time since we updated the current song
        
class SessionUpdater():
    session = None
    def __init__(self, session):
        self.session = session
    
    # Update channel clients with the specified message
    def send_update(self, message):
        if not message:
            return   
        logging.info('send_message to ' + str(self.session.host.user_id() + '_' + self.session.key().id_or_name()) + ': ' + str(message))
        channel.send_message(self.session.host.user_id() + '_' + self.session.key().id_or_name(), message)
        
        for lst in self.session.listeners:
            logging.info('send_message to ' + str(lst.user_id() + '_' + self.session.key().id_or_name()) + ': ' + str(message))
            channel.send_message(lst.user_id() + '_' + self.session.key().id_or_name(), message)

    # Update message for non-incremental updates
    # Returns entire model  
    def get_session_message(self):
        playlist = self.session.playlist
        idx = self.session.curSongIdx

        sessionUpdate = {
            'host': self.session.host.user_id(),
            'hostEmail': self.session.host.email(),
            'play': self.session.play,              # Tell the client to play or not
            'endFlag': self.session.endFlag,         # Session end or not
            'timestamp': time.mktime(self.session.timestamp.timetuple())
        }
        listeners_list = []
        for listener in self.session.listeners:
            listeners_list.append(listener.email())
        sessionUpdate['listeners'] = listeners_list

        if playlist:
            song = Song.get(playlist[idx])
#            sessionUpdate['title']= song.title                  # Current song title
#            sessionUpdate['artist']= song.artist                 # Current song artist
            sessionUpdate['curSongKey']= str(song.blob_key.key())        # Current song blob key. Serve url: /serve/blob_key
            upcomingSongs = []         # send upcoming playlist so new listeners can load songs

            for i in range(idx+1, len(playlist)):
                s = Song.get(playlist[i])
                upcomingSongs.append(str(s.blob_key.key()))
            sessionUpdate['playlist']= upcomingSongs
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
            'endFlag': self.session.endFlag,
            'timestamp': str(time.mktime(self.session.timestamp.timetuple()))
        }
        logging.info('get_song_message: ' + str(sessionUpdate))
        return simplejson.dumps(sessionUpdate)
    
    # Send the most recently added blob key
    def get_blob_message(self, blob_key):
        sessionUpdate = {
            # don't use blob.key() here since we pass that in
            'newSongKey': str(blob_key)
        }
        logging.info('get_blob_message: ' + str(sessionUpdate))
        return simplejson.dumps(sessionUpdate)
    ##############
    # Updating the datastore model
    
    # Song stuff
    # Update song, play, endFlag
    # idx = index into playlist, play = bool, endFlag = bool
    def update_song(self, idx, play, endFlag, timestamp):
        self.session.curSongIdx = idx
        self.session.play = play
        self.session.endFlag = endFlag
        self.session.timestamp = timestamp
        self.session.put()    
        self.send_update(self.get_song_message())
        
        
    # Remove listener from listener list
    def remove_listener(self, user):
        self.session.listeners.remove(user)
        self.session.put()
        listeners = []
        for lst in self.session.listeners:
            listeners.append(lst.email())
            
        sessionUpdate = {
            'listeners': listeners
        }
        message = simplejson.dumps(sessionUpdate)
        self.send_update(message)
        
    # Add song to playlist
    def add_song(self, blob_key_, filename_):
        logging.info('add_song(' + str(blob_key_) + ', ' + str(filename_))
        song = Song(blob_key = blob_key_, filename = filename_)
        song.put()
        self.session.playlist.append(song.key())
        self.session.put()
        
    def remove_session(self):
        # Mark for deletion
        self.session.endFlag = True
        self.session.play = False
        self.session.put()
        self.send_update(self.get_session_message())
        # Delete after 
        for songKey in self.session.playlist:
            logging.info('songKey: ' + str(songKey))
            song = Song.get(songKey)  # Delete playlist from server
            blobstore.delete(song.blob_key.key())
            db.delete(song)
        
        db.delete(self.session)

            
class SessionFromRequest():
    session = None;
    def __init__(self, request):
        user = users.get_current_user()
        session_key = request.get('session_key')
        if user and session_key:
            self.session = Session.get_by_key_name(session_key)
    
    def get_session(self):
        return self.session
    
class SessionListUpdater():
    user = None;
    def __init__(self, request):
        self.user = users.get_current_user()
      
    # Send the message  
    def send_update(self, message):
        ACL = findACL(self.user.user_id())
        for pl in ACL.plisteners:
            session_key = findACL(pl).session_key
            channel.send_message(pl + '_' + session_key, message)
            

#########################################
# Handler code

###########################################
# Session related handlers

# _ah/channel/disconnected
class ChannelDisconnect(webapp.RequestHandler):
    def post(self):
        channel_id = self.request.get('from')
        channel_id = channel_id.split("_", maxsplit=1)
        if (len(channel_id) != 2):
            user = users.User(_user_id = channel_id[0]) # extract user
        logging.info('channel_id: ' + channel_id)
        session_key = channel_id[-1] # extract session key
        session = Session.get_by_key_name(session_key)
        if (session and user in session.listeners):
            SessionUpdater(session).remove_listener(user)
        elif (session and user == session.host):
            SessionUpdater(session).remove_session()
            
# /logout
class Logout(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        # Remove self from current session
        session = SessionFromRequest(self.request).get_session() 
        if (session and user == session.host):
            SessionUpdater(session).remove_session()
        elif (session and user in session.listeners):
            SessionUpdater(session).remove_listener(user)

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
                timestamp = datetime.now()
                if not endFlag:
                    endFlag = False
                if not play:
                    play = True
                SessionUpdater(session).update_song(curIdx, play, endFlag, timestamp)
                
                song = Song.get(session.playlist[curIdx])
                message = { "updateSesStr": str(session.host.email()) + "," + str(session.key().name()) + "," + str(song.filename) 
                }
                SessionListUpdater().send_update(simplejson.dumps(message))   # Send only the change

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
            # TODO: filter wasn't returning any results
            sessionList = Session.all().filter('endFlag =', False).run()
            msg = ""
            for ses in sessionList:
                if ses.curSongIdx < len(ses.playlist):
                    song = Song.get(ses.playlist[ses.curSongIdx])
                    msg += str(ses.host.email()) + "," + str(ses.key().name()) + "," + str(song.filename) + "\n"
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
        filename = self.request.get('filename')
#        title = self.request.get('title')
#        artist = self.request.get('artist')
        if (session and session.host == users.get_current_user()):
            upload_files = self.get_uploads('file')
            if (session.curSongIdx == 0):
                session.timestamp = datetime.now()
                session.put()
                
            blob_info = upload_files[0]
            # add the song to datastore
            SessionUpdater(session).add_song(blob_info.key(), filename)
            # Send message to everyone in the channel with the new blob key
            SessionUpdater(session).send_update(SessionUpdater(session).get_blob_message(blob_info.key()))
        
     
# Serve a song only if the session is valid and if play mode is on
# /serve/___   
class ServeSong(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        session = SessionFromRequest(self.request).get_session()
        blob_key = str(urllib.unquote(blob_key))
        
        # TODO: fix this (we can't load upcoming songs if we check the index)
#        playlist = session.playlist
#        idx = session.curSongIdx
#        song = Song.get(playlist[idx])
#        if (session.endFlag and session.play and (str(song.blob_key) == blob_key)):
        self.send_blob(blobstore.BlobInfo.get(blob_key))

# Request to open the page /open
class OpenPage(webapp.RequestHandler):
    def post(self):
        session = SessionFromRequest(self.request).get_session()
        SessionUpdater(session).send_update(SessionUpdater(session).get_session_message())

# Returns session info for initial join
class SessionInfo(webapp.RequestHandler):
    def get(self):
        session = SessionFromRequest(self.request).get_session()
        self.response.out.write(SessionUpdater(session).get_session_message())

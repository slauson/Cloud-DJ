import urllib
import logging
import time
import datetime

from django.utils import simplejson

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
    return ACLEntry.get_by_key_name(str(userid))

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

###############################################################
# identify by channel ID
class ChannelEntry(db.Model):
    token = db.StringProperty()
    user = db.UserProperty()
    session_key = db.StringProperty()  
    free = db.BooleanProperty()
    expire = db.DateTimeProperty()
    
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
        
        q = ChannelEntry.all().filter('session_key = ', self.session.key().name())
        
        for ch in q.run():
            user_id = ch.user.user_id()

            # handle test users
            if not user_id:
                user_id = ch.user.email()

            logging.info('send_message to ' + str(user_id + '_' + self.session.key().id_or_name()) + ': ' + str(message))
            channel.send_message(ch.key().name(), message)

    # Update message for non-incremental updates
    # Returns entire model  
    def get_session_message(self):
        playlist = self.session.playlist
        idx = self.session.curSongIdx

        # calculate playback offset
        time_diff = datetime.datetime.now() - self.session.timestamp

        sessionUpdate = {
            'type': 'session_update',
            'host': self.session.host.user_id(),
            'hostEmail': self.session.host.email(),
            'play': self.session.play,              # Tell the client to play or not
            'endFlag': self.session.endFlag,         # Session end or not
            'timestamp': str(time_diff.seconds)
        }
        listeners_list = []
        for listener in self.session.listeners:
            listeners_list.append(listener.email())
        sessionUpdate['listeners'] = listeners_list

        if playlist:
            song = Song.get(playlist[idx])

            if song:
    #            sessionUpdate['title']= song.title                  # Current song title
    #            sessionUpdate['artist']= song.artist                 # Current song artist
                sessionUpdate['curSongIdx']= idx                      # Current song index. (Used for reinitializing host on connection loss)
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
        
        if not playlist or idx < 0:
            return
        
        # calculate playback offset
        time_diff = datetime.datetime.now() - self.session.timestamp

        song = Song.get(playlist[idx])
        sessionUpdate = {
#            'title': song.title,
#            'artist': song.artist,
            'type': 'song_update',
            'curSongKey': str(song.blob_key.key()),
            'play': self.session.play,
            'endFlag': self.session.endFlag,
            'timestamp': str(time_diff.seconds)
        }
        logging.info('get_song_message: ' + str(sessionUpdate))
        return simplejson.dumps(sessionUpdate)
    
    # Send the most recently added blob key
    def get_blob_message(self, blob_key):
        sessionUpdate = {
            'type': 'song_upload',
            'newSongKey': str(blob_key.key())
        }
        logging.info('get_blob_message: ' + str(sessionUpdate))
        return simplejson.dumps(sessionUpdate)
    ##############
    # Updating the datastore model
    
    # Song stuff
    # Update song, play, endFlag
    # idx = index into playlist, play = bool, endFlag = bool
    def update_song(self, idx, play, endFlag, timestamp):
        logging.info('update_song: ' + str(idx) + ', ' + str(play) + ', ' + str(endFlag) + ', ' + str(timestamp))
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
            'type': 'remove_listener',
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
        logging.info('remove_session: ' + str(self.session))
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
    def __init__(self):
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
        
        # get channel entry 
        logging.info('ChannelDisconnect: ' + str(channel_id))
        chEntry = ChannelEntry.get_by_key_name(channel_id)
        
        user = chEntry.user
        session_key = chEntry.session_key
        session = Session.get_by_key_name(session_key)
        
        if (session and user == session.host):
            SessionUpdater(session).remove_session()
        elif (session and user in session.listeners):
            SessionUpdater(session).remove_listener(user)
                
        q = Session.all().filter('host =', user)
        for ses in q.run(read_policy=db.STRONG_CONSISTENCY):
            SessionUpdater(ses).remove_session()
            
        chEntry.free = True
        chEntry.put()
        
        # Delete expired entries
        q = ChannelEntry.all().filter('expire <', datetime.datetime.now())
        for expired in q.run():
            db.delete(expired.key())
            
# /logout
class Logout(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        # Remove self from current session
        session = SessionFromRequest(self.request).get_session() 
        logging.info('Logout: ' + str(user) + ', ' + str(session))
        if (session and user == session.host):
            SessionUpdater(session).remove_session()
        elif (session and user in session.listeners):
            SessionUpdater(session).remove_listener(user)
            
        q = Session.all().filter('host =', user)
        for ses in q.run(read_policy=db.STRONG_CONSISTENCY):
            SessionUpdater(ses).remove_session()
            
        q = ChannelEntry.all().filter('user =', user)
        for ch in q.run():
            ch.free = True
            ch.put()

# Make updates to session information
# Message from host
# Control the current song, play or pause, end session
# /update
class UpdateChannel(webapp.RequestHandler):
    def post(self):
        session = SessionFromRequest(self.request).get_session()
        user = users.get_current_user()
        if session:
            logging.info('UpdateChannel stats: ' + str(len(session.listeners)) + ' / ' + str(Session.all().count()))
        else:
            logging.info('UpdateChannel stats: ' + str(0) + ' / ' + str(Session.all().count()))
        logging.info('UpdateChannel: ' + str(self.request))

        if session and user == session.host:
            curIdx = int(self.request.get('curIdx'))   # Index of the current song
            if (int(curIdx) < len(session.playlist)):
                play = int(self.request.get('play')) == 1
                endFlag = int(self.request.get('endflag')) == 1
                num = int(self.request.get('num'))

                timestamp = datetime.datetime.now()
                # use num to offset timestamp so that we account for what has already played
                if play:
                    timestamp = timestamp + datetime.timedelta(0, num)

                SessionUpdater(session).update_song(curIdx, play, endFlag, timestamp)
                
                song = Song.get(session.playlist[curIdx])
                message = { "updateSesStr": str(session.host.email()) + "," + str(session.key().name()) + "," + str(song.filename) 
                }
                # this needs to be sent to all potential listeners
                #SessionListUpdater().send_update(simplejson.dumps(message))   # Send only the change
        logging.info('UpdateChannel stats: ' + str(len(session.listeners)) + ' listeners, ' + str(Session.all().count()) + ' sessions')

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
        logging.info('GetLiveSessions: ' + str(session))
#           user = users.get_current_user()
        if session:
            logging.info('session: ' + str(session.key().id_or_name()))
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
        logging.info('UploadSong: ' + str(filename) + ', ' + str(session))
#        title = self.request.get('title')
#        artist = self.request.get('artist')
        if (session and session.host == users.get_current_user()):
            logging.info('session: ' + str(session.key().id_or_name()) + ', ' + str(session.host))
            upload_files = self.get_uploads('file')

            # automatically play first song so we don't have to send separate update
            if (session.curSongIdx == 0):
                session.timestamp = datetime.datetime.now()
                session.play = True
                session.put()
                
            blob_info = upload_files[0]
            # add the song to datastore
            SessionUpdater(session).add_song(blob_info.key(), filename)
            # Send message to everyone in the channel with the new blob key
            SessionUpdater(session).send_update(SessionUpdater(session).get_blob_message(blob_info))
        
     
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
        logging.info('SessionInfo: ' + str(session))
        
        # when setting up test clients, for some reason their sessions are None
        if not session:
            logging.error('Missing session for request ' + str(self.request))
        else:
            self.response.out.write(SessionUpdater(session).get_session_message())

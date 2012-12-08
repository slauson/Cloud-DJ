
/*
 This file contains global variables and setup methods.
 */

// channel for receiving updates from the server
var channel;

// host of current session
var host;

// this is a list of songs that the user is/will be listening to
var songs = new Array();

// this is a list of potential sessions
var sessions = new Array();

// this is a list of listeners for current session
var listeners = new Array();

// true if user is hosting a session
var hostingSession = false;

var testing = true;

var initialized = false;

/*
 Sets stuff up once the document is fully loaded
 */
function setup() {

	if (!initialized) {
		// setup handlers
		// TODO: setup logout
		$('#logout').click(logout);
		$('#upload_song_form').change(uploadSong);
		
		// setup channel
		createChannel();

		// get upload url
		getUploadUrl();

		initialized = true;
	}

	// setup soundmanager
	if (!soundManager.ok()) {
		soundManager.setup({
			url: '/soundmanager/swf',
			flashVersion: 9,
			useFlashBlock: false,
			onready: function() {
				console.log('soundmanager loaded');

				// add first song if we have one
				if (server_session_cur_song_key) {
					addSong(server_session_cur_song_key);
				}
		
			},
			ontimeout: function() {
				alert('Error loading soundmanager');
			}
		});
	}
	
	if (testing) {
		testSessions();
		testListeners();
	}
}

/*
 Handles server message from channel or other means
 
 Message contents:
  - TODO: sessions: list of sessions (sessionId, host, song)
  - listeners: list of listener usernames
  - song: title of new song in session
  - host: username of host in session
  - TODO: url: url of new song in session
  - endFlag: true if session is being ended

	'host': self.session.host.user_id(),
	'listeners': self.session.listeners,
	'title': song.title,                    # Current song title
	'artist': song.artist,                  # Current song artist
	'curSongKey': str(song.blob_key),       # Current song blob key. Serve url: /serve/blob_key
	'play': self.session.play,              # Tell the client to play or not
	'endFlag': self.session.endFlag         # Session end or not

	'title': song.title,
	'artist': song.artist,
	'curSongKey': str(song.blob_key),
	'play': self.session.play,
	'endFlag': self.session.endFlag
 */
function handleServerMessage(message) {
	
	console.log('handleServerMessage');
	console.log(message.data);

	// fix weird json encoding issues (http://stackoverflow.com/questions/9036429/convert-object-string-to-json)
	message = $.parseJSON(JSON.stringify(eval('(' + message.data + ')')));

	host = message.host;
	
	// update listener list
	// TODO: update incrementally?
	if (message.listeners) {
		listeners = new Array();
		for (idx in message.listeners) {
			listeners.push(new listener(message.listeners[idx]));
		}
		updateListenerList();
	}
	
	if (message.curSongKey) {
		addSong(message.curSongKey);
	}

	if (message.newSongKey) {
		addSong(message.newSongKey);
	}
	
	// session was killed
	if (message.endFlag) {
		alert(host + " has ended the session. Please join or start a session.");
		stopSong();
	}
}

/*
 Populates session list with samples
 */
function testSessions() {
	
	var session1 = new Session(1, 'song 1', 'user1');
	var session2 = new Session(2, 'song 2', 'user2');
	
	sessions = new Array();
	
	sessions.push(session1);
	sessions.push(session2);
	
	updateSessionList();
}

/*
 Populates listener list with samples
 */
function testListeners() {
	var listener1 = new Listener('user1');
	var listener2 = new Listener('user2');
	
	listeners = new Array();
	
	listeners.push(listener1);
	listeners.push(listener2);
	
	updateListenerList();
}

/*
 Returns a nice time string for playback
 */
function getTimeStr(seconds) {
	var minutes = Math.floor(seconds / 60);
	
	var seconds = Math.floor(seconds % 60);
	
	if (seconds < 10) {
		return '' + minutes + ':0' + seconds;
	} else {
		return '' + minutes + ':' + seconds;
	}
}

/*
 Gets upload URL for uploading file from server and updates form action
 */
function getUploadUrl() {
	$.get('/generate_upload_url',
		{},
		function(message) {
			console.log('/generate_upload_url response:' + message);

			$("#upload_song_form").attr("action", message);
		}
	);
	
}

// call setup once document is all loaded
$(document).ready(setup);

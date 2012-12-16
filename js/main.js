
/*
 This file contains global variables and setup methods.
 */

// channel for receiving updates from the server
var channel;

// this is a list of songs that the user is/will be listening to
var songs = new Array();

// this is a list of potential sessions
var sessions = new Array();

// this is a list of listeners for current session
var listeners = new Array();

// this is -1 if not hosting, otherwise the playlist index of the current song
var hostingIndex = -1;

var initialized = false;

/*

variables passed on page load

var server_token = "{{ token }}";
var server_me = "{{ me }}";
var server_session_key = "{{ session_key }}";
var server_session_link = "{{ session_link }}";
var server_session_host = "{{ host }}";
var server_session_listeners = "{{ listeners }}";
var server_session_play = "{{ play }}";
var server_session_end_flag = "{{ endFlag }}";
var server_session_cur_song_key = "{{ curSongKey }}";
 */

/*
   Sets stuff up once the document is fully loaded
 */
function setup() {

	if (!initialized) {
		// setup handlers
		// TODO: setup logout
		$('#logout').click(logout);
		$('#upload_song_form').change(uploadSong);
		$('#toggle_mute').click(userToggleMute);
		$('#pause_button').click(userPauseSong);
		$('#play_button').click(userPlaySong);
		$('#next_button').click(userNextSong);
		//$('#reset_button').click(resetUser);

		// disable buttons until user hosts session
		$('#pause_button').attr('disabled', 'disabled');
		$('#play_button').attr('disabled', 'disabled');
		$('#next_button').attr('disabled', 'disabled');

		// disable upload form if listener
		if (location.href.match('.*session_key.*')) {
			$('#upload_song_form_file').attr('disabled', 'disabled');
		}
		
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
			debugMode: false,	// change this for debugging
			onready: function() {
				console.log('soundmanager loaded');

				// get session details
				getSessionDetails();

				// get sessions
				updateSessionList();
			},
			ontimeout: function() {
				alert('Error loading soundmanager');
			}
		});
	}
}

/*
   Handles server message from channel or other means

   types:
    - update_song
	- remove_listener
	- update_listener
	- remove_session
	- upload_song
	- open_page

   parameters:
    - listeners: list of listeners of session
	- curSongKey: current song key for session
	- hostEmail: email of host
	- curSongIdx: current song index (used to reconnect host)
	- newSongKey: new song added by host (listeners will load in background)
	- endFlag: end session
	- timestamp: time when host started playing current song (used to seek)
	  (this is adjusted to take into account a pause by host on the server side)
 */
function handleServerMessage(message) {
	
	console.log('handleServerMessage');
	console.log(message.data);

	message = message.data;

	// fix weird json encoding issues (http://stackoverflow.com/questions/9036429/convert-object-string-to-json)
	//message = $.parseJSON(JSON.stringify(eval('(' + message.data + ')')));
	while (typeof message == 'string' && message.length > 0) {
		message = JSON.parse(message);
	}

	// get message type
	if (typeof message.type == 'undefined') {
		console.log('Missing message.type');
		return;
	}

	// song update
	if (message.type == 'song_update') {
		songUpdate(message.curSongKey, message.play, message.endFlag, message.timestamp, message.hostEmail, false);
	}
	// session update
	else if (message.type == 'session_update') {
		updateListeners(message.hostEmail, message.listeners);
		updateListenerList();

		//updateSessions

		// check if we need to add a song
		if (songs.length == 0) {

			// hosting
			if (typeof message.curSongIdx != 'undefined' && message.hostEmail && message.hostEmail == server_me_email) {
				console.log('join existing hosted session with index ' + message.curSongIdx);
				hostingIndex = message.curSongIdx

				// enable buttons
				$('#pause_button').removeAttr('disabled');
				$('#play_button').removeAttr('disabled');
				$('#next_button').removeAttr('disabled');

				songUpdate(message.curSongKey, message.play, message.endFlag, message.timestamp, message.hostEmail, true);
			}
			// listening
			else {
				songUpdate(message.curSongKey, message.play, message.endFlag, message.timestamp, message.hostEmail, false);
			}
		}
	}
	// new song added
	else if (message.type == 'song_upload') {
		// add newly uploaded song, play if hosting (for initial upload)
		if (message.newSongKey) {
			addSong(message.newSongKey, 0, hostingIndex != -1 && songs.length == 0, false);

			// update listeners if we are host and we are playing this song
			if (hostingIndex != 0 && songs.length == 1) {
				updateChannel(1, 0, 0);
			}
		}
	}
	else if (message.type == 'open_page') {
		// TODO
	}
}

/*
   Requests and updates available sessions
 */
function getSessionDetails() {
	$.get('/info',
		{'session_key': server_session_key},
		function(message) {
			console.log('/getSessionDetails response:' + message);

			// hack to get handleServerMessage method to work
			var temp = new Object();
			temp.data = message;

			handleServerMessage(temp);
		}
	);
}

/*
   Toggle mute of all songs
 */
function userToggleMute() {
	if (soundManager.ok()) {
		if (songs.length > 0 && songs[0].isMuted()) {
			soundManager.unmute();
		} else {
			soundManager.mute();
		}
	}
}

/*
   Pauses current song, sends update to server.
 */
function userPauseSong() {
	console.log('userPauseSong()');

	// only pause if current song is already playing
	if (!isSongPaused()) {
		pauseSong();

		updateChannel(0, 0, 0);
	}
}

/*
   Plays current song, sends update to server.
 */
function userPlaySong() {
	console.log('userPlaySong(): ' + getSongPlayback());

	// only play if current song is already paused
	if (isSongPaused()) {
		playSong(-1);

		updateChannel(1, 0, -getSongPlayback());
	}
}

/*
   Goes to next song, sends update to server.
 */
function userNextSong() {
	// check if we have another song
	if (songs.length <= 1) {
		alert('Please add another song before skipping.');
	} else {
		nextSong();
	}
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

			$('#upload_song_form').attr('action', message);
		}
	);
}

// call setup once document is all loaded
$(document).ready(setup);

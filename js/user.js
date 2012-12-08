
/*
 This file contains user related objects/methods.
 */


/*
 Listener
 */
function Listener(username) {
	this.username = username;
	
	this.getList = function() {
		return '<li>' + this.username + '</li>';
	}
}

/*
 Session
 */
function Session(sessionId, username, title) {
	this.sessionId = sessionId;
	this.username = username;
	this.title = title;
	
	this.getList = function() {
		return '<li onclick="joinSession(' + this.sessionId + ')"><span class="pointer">'
			+ this.title + ' (' + this.username + ')</span></li>';
	}
}

/*
 ---------------------------------------
 Methods
 ---------------------------------------
 */

/*
 Updates listener list from listener array
 */
function updateListenerList() {
	
	$('#listeners').empty();
	
	for (idx in listeners) {
		$('#listeners').append(listeners[idx].getList());
	}
}

/*
 Updates session list from session array
 */
function updateSessionList() {

	$('#sessions').empty();
	
	for (idx in sessions) {
		$('#sessions').append(sessions[idx].getList());
	}
}


/*
 Send logout request
 Receive confirmation?
 
 Called by logout button handler
 */
function logout() {
	console.log('logout');
	
	stopSong();
	
	// clear songs
	while (songs.length > 0) {
		songs.pop().cleanup();
	}
	
	$.get('/logout',
		{},
		function(message) {
			console.log('/logout response:' + message);
		}
	);
}

/*
 Joins existing session
 
 Called by session list click handler
 */
function joinSession(sessionId) {
	console.log('joinSession');

	stopSong();
	
	// clear songs
	while (songs.length > 0) {
		songs.pop().cleanup();
	}
	
	$.get('/joinSession',
		{sessionId: sessionId},
		function(message) {
			console.log('joinSession response:' + message);
			
			handleServerMessage(message);
		}
	);
}

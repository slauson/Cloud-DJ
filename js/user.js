
/*
 This file contains user related objects/methods.
 */


/*
 Listener
 */
function listener(username) {
	this.username = username;
	
	this.getList = function() {
		return '<li>' + this.username + '</li>';
	}
}

/*
 Session
 */
function session(sessionId, username, title) {
	this.sessionId = sessionId;
	this.username = username;
	this.title = title;
	
	this.getList = function() {
		return '<li class="pointer" onclick="joinSession(' + this.sessionId + ')">'
			+ this.title + ' (' + this.username + ')</li>';
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
	
	$('#listener_list').empty();
	
	for (idx in listeners) {
		var listener = listeners[idx];
		$('#listener_list').append(listener.getList());
	}
}

/*
 Updates session list from session array
 */
function updateSessionList() {

	$('#session_list').empty();
	
	for (idx in sessions) {
		var session = sessions[idx];
		$('#session_list').append(session.getList());
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

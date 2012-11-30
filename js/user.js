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
function session(sessionId, title, username) {
	this.sessionId = sessionId;
	this.title = title;
	this.username = username;
	
	this.getList = function() {
		return '<li class="pointer" onclick="joinSession(' + this.sessionId + ')">'
			+ this.title + ' (' + this.username + ')</li>';
	}
}

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
	
	// stop song
	soundManager.stopAll();
	$('#song_playback').html('');
	currentSong.cleanup();
	
	setup();
	
	// get redirected to login page
}

/*
 Send session id
 Receive song url, position, listener list
 
 Called by session list click handler
 */
function joinSession(sessionId) {
	console.log('joinSession');

	// send request
	
	// show leave session button
	$('#leave_session').show();
	
	// hide start session button
	$('#start_session').hide();
	
	// hide add song form
	$('#upload_song_form').hide();
	
	// update song
	currentSong = new song('15 Step', '/music/15_step.mp3');
	
	// update liseners
	testListeners();
}

/*
 Send session id
 Receive confirmation?
 
 Called by leave session button handler
 */
function leaveSession() {
	console.log('leaveSession');

	// stop music
	soundManager.stopAll();
	$('#song_playback').html('');
	currentSong.cleanup();

	// clear listeners
	$('#listener_list').empty();
	
	// manage buttons
	$('#start_session').show();
	$('#leave_session').hide();
}

/*
 Send start session request
 Receive confirmation
 
 Called by start session button handler
 */
function startSession() {
	console.log('startSession');

	// hide session buttons
	$('#start_session').hide();
	$('#leave_session').hide();

	// show add song form
	$('#upload_song_form').show();
}

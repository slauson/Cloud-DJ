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
	
	// stop song
	soundManager.stopAll();
	$('#song_playback').html('');
	
	if (currentSong) {
		currentSong.cleanup();
	}

	if (testing) {
		setup();
	} else {
		/*
		 request
		 response
		 */
		$.get('/logout',
			{},
			function(data) {
				console.log('/logout response:' + data);
				alert('/logout response: ' + data);
			}
		);
	}
	
	// get redirected to login page
}

/*
 Send session id
 Receive song url, position, listener list
 
 Called by session list click handler
 */
function joinSession(sessionId) {
	console.log('joinSession');

	if (testing) {
		// update song
		currentSong = new song('15 Step', '/music/15_step.mp3', 0);
	
		// update liseners
		testListeners();

		// update session
		hostingSession = false;
		session = new session(sessionId, '15 Step', 'User 1');

		// show leave session button
		$('#leave_session').show();

		// hide start session button
		$('#start_session').hide();

		// hide add song form
		$('#upload_song').hide();

	} else {

		/*
		 request
		  - session_id
		 response
		  - title
		  - url
		  - position
		  - username
		  - listeners list
		 */
		$.get('/joinSession',
			{sessionId: sessionId},
			function(data) {
				console.log('/joinSession response:' + data);

				// update song
				currentSong = new song(data.title, data.url, data.position);
				updateSongInfo();

				// update listeners
				listeners = new Array();
				for (idx in data.listeners) {
					listener = new listener(data.listeners[idx]);
					listeners.push(listener);
				}

				// update session
				hostingSession = false;
				session = new session(sessionId, data.title, data.username);

				// show leave session button
				$('#leave_session').show();
	
				// hide start session button
				$('#start_session').hide();
	
				// hide add song form
				$('#upload_song').hide();
			}
		);

		// TODO: show loading bar?

	}
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

	if (testing) {
		// do nothing
	} else {
		/*
		 request
		  - session_id
		 response
		 */
		$.get('/leaveSession',
			{sessionId: sessionId},
			function(data) {
				console.log('/leaveSession response:' + data);
			}
		);
	}
}

/*
 Send start session request
 Receive confirmation
 
 Called by start session button handler
 */
function startSession() {
	console.log('startSession');

	if (testing) {
		// hide session buttons
		$('#start_session').hide();
		$('#leave_session').hide();

		// show add song form
		$('#upload_song').show();

		hostingSession = true;
	} else {
		/*
		 request
		 response
		  - sessionId
		  - username
		 */
		$.get('/startSession',
			{},
			function(data) {
				console.log('/startSession response:' + data);

				hostingSession = true;

				// hide session buttons
				$('#start_session').hide();
				$('#leave_session').hide();

				// show add song form
				$('#upload_song').show();
			}
		);
	}
}

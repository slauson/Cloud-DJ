
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
		return '<li><span class="pointer" onclick="joinSession(\'' + this.sessionId + '\')">' +
			this.title + ' (' + this.username + ')</span></a></li>';
	}
}

/*
 ---------------------------------------
 Methods
 ---------------------------------------
 */

/*
 Updates listeners from server message
 */
function updateListeners(host_email, listeners_update) {

	console.log('updateListeners(' + host_email + ', ' + listeners_update + ')');

	if (!listeners_update) {
		return;
	}

	listeners = new Array();

	// only add host if its not us
	if (hostingIndex == -1 && host_email && host_email != server_me_email) {
		listeners.push(new Listener(host_email + ' (host)'));
	}

	for (idx in listeners_update) {
		// only add listener entry if its not us
		if (listeners_update[idx] != server_me_email) {
			listeners.push(new Listener(listeners_update[idx]));
		}
	}
}

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
 Updates sessions from server message
 */
function updateSessions(sessions_update) {
	// TODO
}

/*
 Updates session list from session array
 */
function updateSessionList() {

	// request updated session list
	$.get('/sessions',
		{'session_key': server_session_key},
		function(message) {
			console.log('/sessions response:' + message);

			sessions = new Array();

			// update sessions
			var lines = message.split('\n');

			for (idx in lines) {
				if (lines[idx].length > 0) {
					var parts = lines[idx].split(',', 3);

					// only add other sessions
					if (parts[1] != server_session_key) {
						sessions.push(new Session(parts[1], parts[0], parts[2]));
					}
				}
			}

			$('#sessions').empty();

			// no sessions
			if (sessions.length == 0) {
				$('#sessions').append('<li>There are no other active sessions</li>');
			} else {
				for (idx in sessions) {
					$('#sessions').append(sessions[idx].getList());
				}
			}

		}
	);
}

/*
   Joins another user's session, redirecting to new page
 */
function joinSession(sessionId) {
	console.log('joinSession: ' + sessionId);

	// 
	var answer = true;
	
	// if we are in an active session, confirm
	if (songs.length > 0) {
		answer = confirm ('Are you sure you want to leave your current session?');
	}
	
	if (answer) {
		// redirect to other page
		window.location = '/?session_key=' + sessionId;
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
		{'session_key': server_session_key},
		function(message) {
			console.log('/logout response:' + message);

			window.location = server_logout_link
		}
	);
}

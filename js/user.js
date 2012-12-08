
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
					// TODO: don't add own session
					var parts = lines[idx].split(',');
					sessions.push(new Session(parts[1], parts[0], parts[2]));
				}
			}

			$('#sessions').empty();

			// no sessions
			if (sessions.length == 0) {
				$('#sessions').append('<li>There are no current sessions</li>');
			} else {
				for (idx in sessions) {
					$('#sessions').append(sessions[idx].getList());
				}
			}

		}
	);
}

function joinSession(sessionId) {
	console.log('joinSession: ' + sessionId);

	//console.log('redirect to "//?session_key=' + sessionId + '"');
	var answer = confirm ("Are you sure you want to leave your current session?");
	
	if (answer) {
		hostingSession = false;

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
		{},
		function(message) {
			console.log('/logout response:' + message);
		}
	);
}

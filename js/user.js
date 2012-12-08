
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
		return '<li><a href="/?session=' + this.sessionId + '"><span class="pointer">'
			+ this.title + ' (' + this.username + ')</span></a></li>';
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
		{'session': server_session_key},
		function(message) {
			console.log('/sessions response:' + message);

			sessions = new Array();

			// update sessions
			var lines = message.split('\n');

			for (idx in lines) {
				if (lines[idx].length > 0) {
					var parts = lines[idx].split(',');
					sessions.push(new Session(parts[0], parts[0], parts[1]));
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

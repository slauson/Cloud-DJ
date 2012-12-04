
// this is the current song that the user is listening to
var currentSong;

// this is the current session
var currentSession;

// this is a list of potential sessions
var sessions = new Array();

// this is a list of listeners for current session
var listeners = new Array();

var hostingSession = false;

var testing = true;

var initialized = false;

// set stuff up once the document is fully loaded
function setup() {

	if (!initialized) {
		// setup handlers
		$('#leave_session').click(leaveSession);
		$('#start_session').click(startSession);
		$('#logout').click(logout);
		$('#upload_song_form').change(addSong);
		// NOTE: session list click handlers will be set up dynamically
		
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
			},
			ontimeout: function() {
				alert('Error loading soundmanager');
			}
		});
	}
	
	// change visibilities
	$('#start_session').show();
	$('#leave_session').hide();
	$('#upload_song').hide();
	
	if (testing) {
		testSessions();
	}
}

// populate session list with samples
function testSessions() {
	
	var session1 = new session(1, 'song 1', 'user1');
	var session2 = new session(2, 'song 2', 'user2');
	
	sessions = new Array();
	
	sessions.push(session1);
	sessions.push(session2);
	
	updateSessionList();
}

// populate listener list with samples
function testListeners() {
	var listener1 = new listener('user1');
	var listener2 = new listener('user2');
	
	listeners = new Array();
	
	listeners.push(listener1);
	listeners.push(listener2);
	
	updateListenerList();
}

// uses http get request, handles response
function test() {
	$.get('/test',
		{arg1: 1, arg2: 2},
		function(data) {
			console.log(data);
			alert('arg1: ' + data.arg1);
		}
	);
}

function start() {
	if (currentSong != null) {
		currentSong.play();
	}
}

function stop() {
	if (currentSong != null) {
		currentSong.stop();
	}
}

function getTimeStr(seconds) {
	var minutes = Math.floor(seconds / 60);
	
	var seconds = Math.floor(seconds % 60);
	
	if (seconds < 10) {
		return '' + minutes + ':0' + seconds;
	} else {
		return '' + minutes + ':' + seconds;
	}
}

$(document).ready(setup);

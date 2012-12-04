/*
 Song object
 */
function song(title, url, position) {
	this.title = title;
	this.url = url;
	
	this.sound = soundManager.createSound({
		id: title,
		url: url,
		position: position,
		autoLoad: true,
		autoPlay: true,
		onload:function() {
			console.log(this.id + ' done loading');
			$('#song_loading').hide();
		},
		onfinish:function() {
			console.log(this.id + ' done playing');

			// if hosting session, show upload song form
			if (hostingSession) {
				$('#upload_song').show();
			} else {
				getNextSong(currentSession.sessionId);
			}
		},
		whileloading:function() {
			console.log(this.id + ' loading (' + this.bytesLoaded + ' / ' + this.bytesTotal + ')');

			// update loading bar/percentage
			var str = Math.floor((this.bytesLoaded/this.bytesTotal)*100) + '%';

			if (str != $('#song_loading').html) {
				$('#song_loading').html(str);
			}
		},
		whileplaying:function() {
			// update time of song
			var str = getTimeStr(this.position/1000) + ' / ' + getTimeStr(this.duration/1000);
			
			if (str != $('#song_playback').html) {
				$('#song_playback').html(str);
			}
			//console.log(this.id + ' playing (' + this.position + ' / ' + this.duration + ')');
		},
		volume: 50
	});

	// show playback/loading info
	$('#song_playback').show();
	$('#song_loading').show();

	this.cleanup = function() {
		this.sound.destruct();
	}
}

/*
 ---------------------------------------
 Methods
 ---------------------------------------
 */

/*
 Updates song information from current song
 */
function updateSongInfo() {
	if (currentSong) {
		$('#song_title').html(currentSong.title);
	} else {
		$('#song_title').html('');
	}
}

/*
 Send song
 Receive confirmation
 
 Called by add song form handler
 
 Start playing song
 */
function addSong() {
	console.log('addSong');

	if (testing) {
		// hide add song form
		$('#upload_song').hide();
	} else {

		$('#upload_song_form').submit();

		// TODO: handle response

		session = new session(sessionId, 'sample title', 'me');

		// hide add song form
		$('#upload_song').hide();
	}
}

/*
 Send session id
 Receive song url
 
 Called by song onfinish handler
 
 Load/play song
 */
function getNextSong() {
	console.log('getNextSong');

	/*
	 request
	  - session id
	 response
	  - title
	  - url
	 */
	$.get('/song',
		{sessionId: currentSession.sessionId},
		function(data) {
			console.log('/song response:' + data);
			// update song
			currentSong = new song(data.title, data.url, 0);
			updateSongInfo();
		}
	);
}

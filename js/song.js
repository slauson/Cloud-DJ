
/*
 This file contains song related objects/methods.
 */


/*
 ---------------------------------------
 Song object (basically a wrapper around soundmanager2's sound object)
 ---------------------------------------
 */
function song(title, url, position) {
	this.title = title;
	this.url = url;
	
	this.sound = soundManager.createSound({
		id: title,
		url: url,
		position: position,
		autoLoad: false,
		autoPlay: false,
		onload:function() {
			console.log(this.id + ' done loading');
			$('#song_loading').hide();
			
			// load next song
			loadSong();
		},
		onfinish:function() {
			console.log(this.id + ' done playing');

			// hide playback/loading info
			$('#song_playback').hide();
			$('#song_loading').hide();

			// go to next song
			nextSong();
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

	// play song
	this.play = function() {
		this.sound.play();
	}
	
	// stop song
	this.stop = function() {
		this.sound.stop()
	}
	
	// mute song
	this.toggleMute = function() {
		this.sound.toggleMute();
	}
	
	// load song
	this.load = function() {
		this.sound.load();
	}

	// cleanup song
	this.cleanup = function() {
		this.sound.destruct();
	}
	
	// returns true if song is loaded
	this.isLoaded = function() {
		return this.sound.loaded;
	}
	
	// returns true if song is loading
	this.isLoading = function() {
		return this.sound.bytesLoaded > 0 && this.sound.bytesLoaded < this.sound.bytesTotal;
	}
}

/*
 ---------------------------------------
 Methods
 ---------------------------------------
 */

/*
 Start current song
 */
function startSong() {
	if (songs.length > 0) {
		songs[0].play();
	}
}

/*
 Stop current song
 */
function stopSong() {
	if (songs.length > 0) {
		songs[0].stop();
	}
}

/*
 Toggle mute of current song
 */
function toggleMuteSong() {
	if (songs.length > 0) {
		songs[0].toggleMute();
	}
}

/*
 Loads next song if possible
 */
function loadSong() {
	for (idx in songs) {
		// check if song is not loaded yet
		if (!songs[idx].isLoaded()) {
			// start loading if song is not already loading
			if (!songs[idx].isLoading()) {
				songs[idx].load();
			}
			// return in either case
			return;
		}
	}	
}

/*
 Plays next song if possible
 */
function nextSong() {

	if (songs.length > 0) {
	
		songs.pop().cleanup();
		
		// check if song list is empty
		if (songs.length == 0) {
			if (hostingSession) {
				alert("Please choose another song to continue your session.");
			} else {
				alert("Session host has not chosen the next song.");
			}
		}
		// otherwise play next song
		else {
			songs[0].play();
		}
	}
}


/*
 Upload song to server
 */
function uploadSong() {
	console.log('addSong');

	$('#upload_song_form').submit();

	/*
	 TODO: handle response
	 - add song
	 - start playing
	*/
}

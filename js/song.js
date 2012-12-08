
/*
 This file contains song related objects/methods.
 */


/*
 ---------------------------------------
 Song object (basically a wrapper around soundmanager2's sound object)
 ---------------------------------------
 */
function Song(title, url, position) {
	console.log('new Song: ' + title + ', ' + url + ', ' + position);
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
		onid3:function() {
			console.log('onid3: ' + this.playState);

			for (prop in this.id3) {
				console.log(prop + ': ' + this.id3[prop]);
			}

			// update properties is song is already playing
			if (this.playState == 1) {
				setProperties();
			}
		},
		volume: 50
	});

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
	
	// returns list string
	this.getList = function() {
		return '<li>' + this.title + '</li>';
	}

	// set song properties
	this.setProperties = function() {
		console.log('setProperties');
		var title = '';
		var artist = '';
		var album = '';

		if (!this.sound.id3) {
			console.log('setProperties id3 not ready');
			return;
		}

		if ('tit2' in this.sound.id3) {
			title = this.sound.id3['tit2'];
		}

		if ('tpe2' in this.sound.id3) {
			artist = this.sound.id3['tpe2'];
		} else if ('tpe1' in this.sound.id3) {
			artist = this.sound.id3['tpe1'];
		} else if ('tcom' in this.sound.id3) {
			artist = this.sound.id3['tcom'];
		}

		if ('talb' in this.sound.id3) {
			album = this.sound.id3['talb'];
		}

		if (title != '') {
			$('#song_title').html(title);
		}
		if (artist != '') {
			$('#song_artist').html(artist);
		}
		if (album != '') {
			$('#song_album').html(album);
		}
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

		// show playback/loading info
		$('#song_playback').show();
		$('#song_loading').show();

		songs[0].setProperties();
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
			startSong();
		}
	}
}

/*
 Updates song list from song array
 */
function updateSongList() {

	$('#songs').empty();
	
	for (idx in songs) {
		if (idx != 0) {
			$('#songs').append(songs[idx].getList());
		}
	}
}

/*
 Upload song to server
 */
function uploadSong() {
	console.log('uploadSong');

	hostingSession = true;
	
	// fill in other args before upload
	$('#upload_song_form_title').val($('#upload_song_form_file').val().replace('C:\\fakepath\\', ''));
	$('#upload_song_form_artist').val($('#upload_song_form_file').val().replace('C:\\fakepath\\', ''));
	$('#upload_song_form_session_key').val(server_session_key);

	// set file upload action
	//$("#upload_song_form").attr("action", server_upload_url);	

	// do file upload
	$('#upload_song_form').submit();

	// TODO: clear filename in input form
}

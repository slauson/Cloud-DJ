
/*
 This file contains song related objects/methods.
 */


/*
 ---------------------------------------
 Song object (basically a wrapper around soundmanager2's sound object)
 ---------------------------------------
 */
function Song(id, url, index, position) {
	console.log('new Song: ' + id + ', ' + url + ', ' + index + ', ' + position);
	this.id = id;
	this.url = url;

	// index within playlist on server
	this.index = index;

	parentThis = this;
	
	this.sound = soundManager.createSound({
		id: id,
		url: url,
		position: position,
		autoLoad: false,
		autoPlay: false,
		onload:function() {
			console.log(this.id + ' done loading');
			//$('#song_loading').hide();
			
			// load next song
			loadSong();
		},
		onfinish:function() {
			console.log(this.id + ' done playing');

			// hide playback/loading info
			//$('#song_playback').hide();
			//$('#song_loading').hide();

			// go to next song
			nextSong();
		},
		whileloading:function() {
			console.log(this.id + ' loading (' + this.bytesLoaded + ' / ' + this.bytesTotal + ')');

			// update loading bar/percentage
			var str = Math.floor((this.bytesLoaded/this.bytesTotal)*100) + '% Loaded';

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

			// update properties if song is already playing
			if (this.playState == 1) {
				parentThis.setProperties();
			}
			// otherwise update up next list
			else {
				updateSongList();
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
		return '<li>' + this.getTitle() + ' - ' + this.getArtist() + '</li>';
	}

	this.getTitle = function() {
		var title = '?';

		if ('TIT2' in this.sound.id3) {
			title = this.sound.id3['TIT2'];
		}

		return title;
	}

	this.getArtist = function() {
		var artist = '?';

		if ('TPE2' in this.sound.id3) {
			artist = this.sound.id3['TPE2'];
		} else if ('TPE1' in this.sound.id3) {
			artist = this.sound.id3['TPE1'];
		} else if ('TCOM' in this.sound.id3) {
			artist = this.sound.id3['TCOM'];
		}

		return artist;
	}

	this.getAlbum = function() {
		var album = '?';

		if ('TALB' in this.sound.id3) {
			album = this.sound.id3['TALB'];
		}

		return album;
	}

	// set song properties
	this.setProperties = function() {
		console.log('setProperties: ' + this.id);

		$('#song_title').html(this.getTitle());
		$('#song_artist').html(this.getArtist());
		$('#song_album').html(this.getAlbum());
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

	// TODO: check for more songs on server

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
				// TODO: send update to server
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
 Adds song to list if we don't already have it
 */
function addSong(url) {
	// update current song info
	var containsSong = false;
	// check if we have the song already
	for (idx in songs) {
		if (songs[idx].url == url) {
			containsSong = true;
			break;
		}
	}

	// if not, add it to list
	if (!containsSong) {
		// TODO: set id, index
		songs.push(new Song(url, 'serve/' + url, 0, 0));
		loadSong();
		updateSongList();
		
		// play song immediately if its the only song
		if (songs.length == 1) {
			startSong();
		}
	}
}

/*
 Upload song to server
 */
function uploadSong() {
	console.log('uploadSong');

	// if listener, leave session, start new session
	if (server_session_host != server_me) {
		// TODO
	}

	// add another song to playlist

	// fill in other args before upload
	$('#upload_song_form_filename').val($('#upload_song_form_file').val().replace('C:\\fakepath\\', ''));
	$('#upload_song_form_session_key').val(server_session_key);

	// do file upload
	$('#upload_song_form').submit();

	// get new upload url
	getUploadUrl();

	// clear filename in input form
	$('#upload_song_form')[0].reset();
}

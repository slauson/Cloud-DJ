
/*
   This file contains song related objects/methods.
 */


/*
   ---------------------------------------
   Song object (basically a wrapper around soundmanager2's sound object)
   ---------------------------------------
 */
function Song(id, url, position) {
	console.log('new Song: ' + id + ', ' + url + ', ' + position);
	this.id = id;
	this.url = url;

	this.sound = soundManager.createSound({
		id: id,
		url: url,
		position: position*1000,
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

			// go to next song

			// wait for host update before going to next song
			nextSong();
		},
		whileloading:function() {
			console.log(this.id + ' loading (' + this.bytesLoaded + ' / ' + this.bytesTotal + ')');

			// update loading bar/percentage only if song is currently playing
			if (this.playState == 1 || this.paused) {
				var str = Math.floor((this.bytesLoaded/this.bytesTotal)*100) + '% Loaded';

				if (str != $('#song_loading').html) {
					$('#song_loading').html(str);
				}
			}
		},
		whileplaying:function() {
			// update time of song
			var str = getTimeStr(this.position/1000) + ' / ' + getTimeStr(this.duration/1000);
			
			if (str != $('#song_playback').html && this.position < this.duration && !this.paused) {
				$('#song_playback').html(str);
			}
		},
		onid3:function() {
			console.log('onid3: ' + this.playState);

			for (prop in this.id3) {
				console.log(prop + ': ' + this.id3[prop]);
			}

			// update properties if song is already playing or is paused
			if (this.playState == 1 || this.paused) {
				setSongProperties();
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
	
	// pause song
	this.pause = function() {
		this.sound.pause()
		$('#song_playback').html($('#song_playback').html() + ' (Paused)');
	}

	// returns true if song is paused
	this.isPaused = function() {
		return this.sound.paused;
	}

	// returns true if sound is muted
	this.isMuted = function() {
		return this.sound.muted;
	}

	// return current playback position in seconds
	this.getPlayback = function() {
		console.log('getPlayback: ' + this.sound.position);
		return Math.floor(this.sound.position / 1000);
	}

	// mute song
	this.toggleMute = function() {
		this.sound.toggleMute();
	}
	
	// load song
	this.load = function() {
		this.sound.load();
	}

	// sets song position in seconds
	// only actually sets position if we have loaded data up to that point
	this.setPosition = function(offset) {
		console.log('setPosition(' + offset + ')');
		if (offset != 0 && (typeof this.sound.loaded == 'undefined' ||
				!this.sound.loaded || (this.sound.duration && offset * 1000 < this.sound.duration)))
		{
			this.sound.setPosition(offset * 1000);
		}
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
		var title = 'Unknown Title';

		if ('TIT2' in this.sound.id3) {
			title = this.sound.id3['TIT2'];
		}

		return title;
	}

	this.getArtist = function() {
		var artist = 'Unknown Artist';

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
		var album = 'Unknown Album';

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
   1355122331.0,
   1355122357.0
   1355122388.0
 */

/*
   Play current song
 */
function playSong(offset) {
	console.log('playSong(' + offset + ')');

	if (songs.length > 0) {

		// only set position if song is paused and at beginning
		if (offset >= 0 && songs[0].isPaused() && songs[0].getPlayback() < 2) {
			songs[0].setPosition(offset);
		}

		songs[0].play();

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
   Stop current song
 */
function stopSong() {
	if (songs.length > 0) {
		songs[0].stop();
	}
}

/*
   Pause current song
 */
function pauseSong() {
	if (songs.length > 0) {
		songs[0].pause();
	}
}

/*
   Returns current song playback in seconds
 */
function getSongPlayback() {
	if (songs.length > 0) {
		return songs[0].getPlayback();
	} else {
		return 0;
	}
}

/*
   Returns true if current song is paused
 */
function isSongPaused() {
	return songs.length == 0 || songs[0].isPaused();
}
/*
   Updates song title, artist, album
 */
function setSongProperties() {
	if (songs.length > 0) {
		songs[0].setProperties();
	}
}

/*
   Loads next song if possible
 */
function loadSong() {
	console.log('loadSong');

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
	console.log('nextSong');

	if (songs.length > 0) {
		songs.shift().cleanup();
		
		// check if song list is empty
		if (songs.length == 0) {
			if (hostingIndex != -1) {
				alert('Please choose another song to continue your session.');
				// TODO: send some kind of update to server?
			} else {
				alert('Session host has not chosen the next song.');
			}
		}
		// otherwise play next song
		else {

			if (hostingIndex != -1) {
				hostingIndex++;
				console.log('increment hostingIndex next song: ' + hostingIndex);
				updateChannel(1, 0, 0);
			}
			playSong(0);
		}

		updateSongList();
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
   Adds song to list if we don't already have it.
   This also plays pauses existing songs.
    - url: url of song to add
    - offset: offset of playing song
    - play: play song
    - setCurrent: song is new current song (host skipped song)
 */
function addSong(url, offset, play, setCurrent) {
	console.log('addSong(' + url + ', ' + offset + ', ' + play + ', ' + setCurrent + ')');
	
	// update current song info
	var containsSongIndex = -1;

	// check if we have the song already
	for (idx in songs) {
		if (songs[idx].id == url) {
			containsSongIndex = idx;
			break;
		}
	}

	console.log('containsSongIndex:\t' + containsSongIndex);

	// we don't have song, add it to list
	if (containsSongIndex == -1) {
		songs.push(new Song(url, 'serve/' + url, offset));
		loadSong();

		// if we get a force play, stop current song, cleanup all songs
		if (setCurrent) {
			console.log('\tremoving any existing songs from playlist (do not have song)');
			stopSong();

			while (songs.length > 1) {
				songs.shift().cleanup();
			}
		}

		updateSongList();
		
		// play song immediately if its the only song
		if (songs.length == 1) {
			if (play) {
				playSong(offset);
			}
			else {
				pauseSong();

				// update song properties
				setSongProperties();
			}
		}
	}
	// we have song and its currently playing
	else if (containsSongIndex == 0) {
		if (play) {
			playSong(offset);
		} else {
			pauseSong();
		}
	}
	// we have song in the playlist
	else {
		
		if (setCurrent) {
			console.log('\tremoving songs from playlist (have song)');
			stopSong();

			var temp = containsSongIndex;

			while (temp > 0) {
				songs.shift().cleanup();
				temp--;
			}

			updateSongList();

			if (play) {
				playSong(offset);
			}
		}
	}

}

/*
   Upload song to server
 */
function uploadSong() {
	console.log('uploadSong');

	// TODO: leave session if currently in someone else's session
	if (hostingIndex == -1) {
		hostingIndex = 0;
	} else if (songs.length == 0) {
		hostingIndex++;
		console.log('increment hostingIndex upload song: ' + hostingIndex);
	}

	// fill in other args before upload
	$('#upload_song_form_filename').val($('#upload_song_form_file').val().replace('C:\\fakepath\\', ''));
	$('#upload_song_form_session_key').val(server_session_key);

	// do file upload
	$('#upload_song_form').submit();

	// get new upload url
	getUploadUrl();

	// clear filename in input form
	$('#upload_song_form')[0].reset();

	// enable pause/play/next buttons
	$('#pause_button').removeAttr('disabled');
	$('#play_button').removeAttr('disabled');
	$('#next_button').removeAttr('disabled');
}

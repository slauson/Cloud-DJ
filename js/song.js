
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

			// hide playback/loading info
			//$('#song_playback').hide();
			//$('#song_loading').hide();

			// go to next song

			// wait for host update before going to next song
			nextSong();
		},
		whileloading:function() {
			console.log(this.id + ' loading (' + this.bytesLoaded + ' / ' + this.bytesTotal + ')');

			// update loading bar/percentage only if song is currently playing
			if (this.playState == 1) {
				var str = Math.floor((this.bytesLoaded/this.bytesTotal)*100) + '% Loaded';

				if (str != $('#song_loading').html) {
					$('#song_loading').html(str);
				}
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
		if (offset != 0 && (typeof this.sound.loaded == "undefined" ||
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
 */

/*
 Start current song
 */
function startSong(offset) {
	console.log('startSong(' + offset + ')');

	if (songs.length > 0) {
		//songs[0].setPosition(offset);
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
	console.log('nextSong');

	if (songs.length > 0) {
		songs.shift().cleanup();
		
		// check if song list is empty
		if (songs.length == 0) {
			if (hostingIndex != -1) {
				alert("Please choose another song to continue your session.");
				// TODO: send update to server
			} else {
				alert("Session host has not chosen the next song.");
			}
		}
		// otherwise play next song
		else {

			if (hostingIndex != -1) {
				updateChannel();
			}
			startSong(0);
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
 Adds song to list if we don't already have it
  - url: url of song to add
  - offset: offset of playing song
  - forcePlay: force song to play immediately (host skipped song or we just joined session)
 */
function addSong(url, offset, forcePlay) {
	console.log('addSong(' + url + ', ' + offset + ', ' + forcePlay + ')');

	// update current song info
	var containsSong = false;
	// check if we have the song already
	for (idx in songs) {
		if (songs[idx].url == url) {
			containsSong = true;
			break;
		}
	}

	// TODO: handle forcePlay with more than one song in playlist

	// if not, add it to list
	if (!containsSong) {
		songs.push(new Song(url, 'serve/' + url, offset));
		loadSong();
		updateSongList();
		
		// play song immediately if its the only song
		if (songs.length == 1) {
			startSong(offset);
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
		
	}

	hostingIndex++;

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

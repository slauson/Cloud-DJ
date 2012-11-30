/*
 Song object
 */
function song(title, url) {
	this.title = title;
	this.url = url;
	
	this.sound = soundManager.createSound({
		id: title,
		url: url,
		autoLoad: true,
		autoPlay: true,
		onload:function() {
			console.log(this.id + ' done loading');
		},
		onfinish:function() {
			console.log(this.id + ' done playing');
		},
		whileloading:function() {
			console.log(this.id + ' loading (' + this.bytesLoaded + ' / ' + this.bytesTotal + ')');
		},
		whileplaying:function() {
			var str = getTimeStr(this.position/1000) + ' / ' + getTimeStr(this.duration/1000);
			
			if (str != $('#song_playback').html) {
				$('#song_playback').html(str);
			}
			//console.log(this.id + ' playing (' + this.position + ' / ' + this.duration + ')');
		},
		volume: 50
	});
	
	this.cleanup = function() {
		this.sound.destruct();
	}
}

function updateSongInfo() {
	$('#song_title').html(currentSong.title);
}

/*
 Send song
 Receive confirmation
 
 Called by add song form handler
 
 Start playing song
 */
function addSong() {
	console.log('addSong');

	// hide add song form
	$('#upload_song_form').hide();
}

/*
 Send session id
 Receive song url
 
 Called by song onfinish handler
 
 Load/play song
 */
function getNextSong() {
	console.log('getNextSong');

	// if host, show upload song form
}

/*function song(title, basename, numParts) {
	this.title = title;
	this.basename = basename;
	this.numParts = numParts;
	
	// last part that's been loaded
	this.loadPart = -1;
	
	// part that's currently playing
	this.playPart = -1;
	
	// array of sounds to play in sequence
	this.sounds = new Array();
	
	// create sounds
	for (var i = 1; i <= numParts; i++) {
		var sound = soundManager.createSound({
			id: basename + '-0' + i,
			url: '/music/split-audacity/' + basename + '-0' + i + '.mp3',
			//autoLoad: false,
			//autoPlay: false,
			multiShot: false,
			onload:function() {
				currentSong.loadNext();
			},
			onfinish:function() {
				currentSong.playNext();
			},
			whileplaying:function() {
				console.log(this.id + ', ' + this.position + ', ' + this.duration);
			},
			volume: 50
		});
		
		this.sounds.push(sound);
	}

	this.loadNext = function() {
		console.log('song loadNext ' + this.loadPart + ' < ' + this.numParts);
		if (this.loadPart < this.numParts) {
			this.loadPart++;
			this.sounds[this.loadPart].load();
		}
	}
	
	this.playNext = function() {
		console.log('song playNext ' + this.playPart + ' < ' + this.numParts);
		if (this.playPart < this.numParts) {
			this.playPart++;
			this.sounds[this.playPart].play();
		}
	}

	this.load = function() {
		console.log('song load');
		if (this.loadPart == 0) {
			this.sounds[0].load();
		}
	}
	
	this.play = function() {
		console.log('song play');
		this.playPart = 0;
		this.sounds[0].play();
	}
	
	this.stop = function() {
		this.sounds[this.playPart].stop();
		this.playPart = 0;
	}
		
}*/

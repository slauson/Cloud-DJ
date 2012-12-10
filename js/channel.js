
/*
  This file contains channel related objects/methods.
 */


/*
   Create channel from server token
 */
function createChannel() {
	channel = new goog.appengine.Channel(server_token);
    socket = channel.open();
    socket.onopen = channelOnOpen;
    socket.onmessage = channelOnMessage;
    socket.onerror = channelOnError;
    socket.onclose = channelOnClose;
}

channelOnOpen = function() {
	console.log('channel opened');
}

channelOnMessage = function(message) {
	console.log('channelOnMessage');
	
	handleServerMessage(message);	
}

channelOnError = function(error) {
	console.log('channel error: ' + error.description + '(' + error.code + ')');
}

channelOnClose = function() {
	console.log('channel closed');
}

/*
   Updates channel when user is host
 */
function updateChannel(play, endflag, num) {
	$.post('/update',
		{'session_key': server_session_key, 'curIdx': hostingIndex, 'play': play, 'endflag': endflag, 'num': num},
		function(message) {
			console.log('/update response:' + message);
		}
	);
}

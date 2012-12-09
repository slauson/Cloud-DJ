
/*
 This file contains channel related objects/methods.
 */


// create channel from server token
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
	console.log('channel message: ' + message);
	
	handleServerMessage(message);	
}

channelOnError = function(error) {
	alert('channel error: ' + error.description + '(' + error.code + ')');
}

channelOnClose = function() {
	console.log('channel closed');
}

/*
 Updates channel when user is host
 */
function updateChannel() {
	$.post('/update',
		{'curIdx': hostingIndex, 'play': true, 'endflag': false, 'session_key': server_session_key},
		function(message) {
			console.log('/update response:' + message);
		}
	);
}

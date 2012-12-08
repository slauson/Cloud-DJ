
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
	console.log('channel error: ' + error);
	console.log(error);
	
	alert("Channel error (check js console)");
}

channelOnClose = function() {
	console.log('channel closed');
	
	alert("Channel closed");
}

"""

Client test helper.

"""

import httplib2
import socket
import time

# what url to call
URL = 'http://localhost:8080/?testing'
#URL = 'http://localhost:8080/?testing&session_key=7W361kcaNf'

http = httplib2.Http(timeout=10)

try:
	# send request
	response, content = http.request(URL)

	# check status
	if response.status != 200:
		print "Response not OK"
	else:
		print 'OK'
except socket.timeout:
	print 'Error socket timeout'

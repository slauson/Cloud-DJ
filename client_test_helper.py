"""

Client test helper.

"""

import httplib2
import socket
import time

# what url to call
URL = 'http://localhost:8080/?testing'

http = httplib2.Http(timeout=30)

try:
	# send request
	resp, content = http.request(URL)

	# check status
	if resp.status != 200:
		print "Response not OK"
	else:
		print 'OK'
except socket.timeout:
	print 'Error socket timeout'

"""

Client test helper.

0
5
10
20
30
40
50
60
70
80
90
100

todo: add timing information before/after request

Key Name

"""

import httplib2
import socket
import time

# what url to call
#URL = 'http://localhost:8080/?testing'
URL = 'http://4.cloud-dj.appspot.com/?testing'
#URL = 'http://3.cloud-dj.appspot.com/_ah/channel/disconnected/?from=AHRlWrogKWHKR7SLjsiVCKNl4PlWRnpYGdh66LFR8NcNR-YC0lK0KpJB0mleGvNwF7Jwz5JXLp4_YKFeQszd_Wi4iP6WITGy3lBFc8SgonlDSuDwMuNqWKTwlXAXGzVvLWAEbgtB2Q2T'
#URL = 'http://localhost:8080/?testing&session_key=7W361kcaNf'

http = httplib2.Http(timeout=10)

fout = open('test1_timing.txt', 'a+')

try:
	time_before = int(round(time.time() * 1000))

	# send request
	response, content = http.request(URL)

	# check status
	if response.status != 200:
		print "Response not OK"
		print content
	else:
		print 'OK'

	time_elapsed = int(round(time.time() * 1000)) - time_before
	print str(time_elapsed)

	fout.write("%d\n" % time_elapsed)
except socket.timeout:
	print 'Error socket timeout'

fout.close()

"""Simple web application load testing script.

This is a simple web application load
testing skeleton script. Modify the code between !!!!!
to make the requests you want load tested.
"""
import sys
import timeit
import httplib2
import random
import socket
import time
from threading import Event
from threading import Thread
from threading import current_thread
from urllib import urlencode

# Modify these values to control how the testing is done

# Which URL to call to join a session
URL = 'http://4.cloud-dj.appspot.com/?testing&session_key=m7o6SU6BYO'
#URL = 'http://localhost:8080/?testing&session_key=SINFXmx4tp'

# How many threads should be running at peak load for the hardest test
NUM_THREADS = 100

# How long each thread should sleep before waking up to test if endEvent is set
THREAD_SLEEP_TIME = 30 # seconds

# How many times to run test to take average response time
REPS = 1 # (each time creates a new user, and hence a new channel, so can't do more than once)

# How many minutes the test should run with all threads active.
TIME_AT_PEAK_QPS = 1 # minutes

# How many seconds to wait between starting threads.
# Shouldn't be set below 30 seconds.
DELAY_BETWEEN_THREAD_START = 60 # seconds

# Which file to append timing results to
results_filename = "nthListenerTime/deployed_time5.txt"

h = httplib2.Http(timeout=30)
quitevent = Event()

def threadproc(N, results_file):
    """
    This function is executed by each thread.
    
    N is how many total threads there will be at max load.
    We're only interested in how long that one takes.

    results_file is where to write the timing information for the N-th thread
    """
    print "Thread started: %s" % current_thread().getName()
    sys.stdout.flush()
    h = httplib2.Http(timeout=30)
    firsttime = True
    while not quitevent.is_set():
        if firsttime:
            try:
                firsttime = False
                print "entered try in thread"
                sys.stdout.flush()
                # TIME HOW LONG IT TAKES TO MAKE REPS HTTP REQUESTS OF THE SERVER
                total = timeit.timeit("resp, content = h.request('%s')"%URL, 
                                      "import httplib2; h = httplib2.Http(timeout=30)", 
                                      number=REPS)
                results_file.write("%s\t%0.19f\n"%(current_thread().getName(), (total/REPS)))
                results_file.flush()
            except socket.timeout:
                pass
        else:
            #resp, content = h.request(URL) # would create a new user 
            time.sleep(THREAD_SLEEP_TIME)

    print "Thread finished: %s" % current_thread().getName()
    sys.stdout.flush()

def loadN(N, results_file):
    """
    Generate N threads to create load, time the latest listener, the N-th thread
    and write it to the results_file.
    """
    # runtime = (time running all threads + time to start all the threads)
    runtime = (TIME_AT_PEAK_QPS * 60 + DELAY_BETWEEN_THREAD_START * N)
    print "Total runtime will be: %d seconds" % runtime
    sys.stdout.flush()
    threads = []
    try:
        for i in range(N):
            t = Thread(target=threadproc, args = (N, results_file))
            t.start()
            threads.append(t)
            time.sleep(DELAY_BETWEEN_THREAD_START)
        print "All threads running"
        sys.stdout.flush()
        time.sleep(TIME_AT_PEAK_QPS*60)
        print "Completed full time at peak qps, shutting down threads"
        sys.stdout.flush()
    except:
        print "Exception raised, shutting down threads"
        sys.stdout.flush()

    quitevent.set()
    time.sleep(3)
    for t in threads:
        t.join(1.0)
    print "Finished"
    sys.stdout.flush()


if __name__ == "__main__":
    # open results file for append
    f = open(results_filename, "a+")
    if not f:
        print "file didn't open"
        sys.stdout.flush()
        exit()

    # Run NUM_THREADS threads, with each addition timing how long it takes to run
    loadN(NUM_THREADS, f)

    f.close()





#    MODIFIED FROM WEBSITE
#    https://developers.google.com/appengine/articles/load_test?hl=en
#    Copyright 2009 Google Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

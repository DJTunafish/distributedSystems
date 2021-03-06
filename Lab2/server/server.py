# coding=utf-8
#------------------------------------------------------------------------------------------------------
# TDA596 Labs - Server Skeleton
# server/server.py
# Input: Node_ID total_number_of_ID
# Student Group:
# Student names: Erik Jungmark & Patrick Franz
#------------------------------------------------------------------------------------------------------
# We import various libraries
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler # Socket specifically designed to handle HTTP requests
import sys # Retrieve arguments
import re # Use to pattern match routes
from urlparse import parse_qs # Parse POST data
from httplib import HTTPConnection # Create a HTTP connection, as a client (for POST requests to the other vessels)
from urllib import urlencode # Encode POST content into the HTTP header
from codecs import open # Open a file
from threading import  Thread # Thread Management
from random import randint
from time import sleep
import time
#------------------------------------------------------------------------------------------------------

# Global variables for HTML templates
board_frontpage_footer_template = ""
board_frontpage_header_template = ""
boardcontents_template = ""
entry_template = ""
#nodeId = -1

AUTHORS = "Erik Jungmark & Patrick Franz"

BOARD_MESSAGE = "Who runs Barter Town?"

#------------------------------------------------------------------------------------------------------
# Static variables definitions
PORT_NUMBER = 80
#------------------------------------------------------------------------------------------------------




#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class BlackboardServer(HTTPServer):
    #------------------------------------------------------------------------------------------------------
    def __init__(self, server_address, handler, node_id, vessel_list, rank):
        # We call the super init
        HTTPServer.__init__(self,server_address, handler)
        # we create the dictionary of values
        self.store = {}
        # We keep a variable of the next id to insert
        self.current_key = 0
        # our own ID (IP is 10.1.0.ID)
        self.vessel_id = vessel_id
        # The list of other vessels
        self.vessels = vessel_list
        self.rank   = rank
        self.leader = False
        self.leader_vessel = ""
        self.t_0 = 0
        self.t_total = 0
#------------------------------------------------------------------------------------------------------
    # We add a value received to the store
    #value: value to be added to the store
    #Adds a value to the store
    #Returns key of the value
    def add_value_to_store(self, value, key=None):
        # We add the value to the store
        if key == None:
            key = self.current_key
            self.current_key += 1
        elif key >= self.current_key:
            self.current_key = key + 1

        self.store[key] = value
        return key
#------------------------------------------------------------------------------------------------------
    # We modify a value received in the store, if the key exists
    # key   = key of the value to modify
    # value = new value
    def modify_value_in_store(self,key,value):
        if key in self.store:
            self.store[key] = value
#------------------------------------------------------------------------------------------------------
    # We delete a value received from the store, if it exists in the store
    # key = key of value to delete
    def delete_value_in_store(self,key):
        self.store.pop(key, None)
#------------------------------------------------------------------------------------------------------
    # Contact a specific vessel with a set of variables to transmit to it, via
    # an HTTP POST request
    # vessel_ip = ip of the vessel to contact
    # path      = path to send the HTTP request to
    # data      = dictionary of values to include in the post request
    def contact_vessel(self, vessel_ip, path, data):
        # the Boolean variable we will return
        success = False

        #Add a propagation flag to the data, to indicate that the vessel
        #should not propagate the received valeus further
        post_content = urlencode(data)
        # the HTTP header must contain the type of data we are transmitting, here URL encoded
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        # We should try to catch errors when contacting the vessel
        try:
            # We contact vessel:PORT_NUMBER since we all use the same port
            # We can set a timeout, after which the connection fails if nothing happened
            connection = HTTPConnection("%s:%d" % (vessel_ip, PORT_NUMBER), timeout = 30)
            # We only use POST to send data (PUT and DELETE not supported)
            action_type = "POST"
            # We send the HTTP request
            connection.request(action_type, path, post_content, headers)
            # We retrieve the response
            response = connection.getresponse()
            # We want to check the status, the body should be empty
            status = response.status
            # If we receive a HTTP 200 - OK
            if status == 200:
                success = True
            # We catch every possible exceptions
        except Exception as e:
            print "Error in contact_vessel while contacting %s" % vessel_ip
            # printing the error given by Python
            print(e)
            print repr(e)

        # we return if we succeeded or not
        return success
#------------------------------------------------------------------------------------------------------
    # We send a received value to all the other vessels of the system, via HTTP
    # POST requests
    # path = path to send the POST request to
    # data = dictionary of vaues to include in the POST requests
    def propagate_value_to_vessels(self, path, data):
        # We iterate through the vessel list
        for vessel in self.vessels:
            # We should not send it to our own IP, or we would create an infinite loop of updates
            if vessel != ("10.1.0.%s" % self.vessel_id):
                # A good practice would be to try again if the request failed
                # Here, we do it only once
                thread = Thread(target=self.contact_vessel,
                                args=(vessel, path, data))
                thread.daemon = True
                thread.start()
                #self.contact_vessel(vessel, path, data)

    def contact_leader(self, path, data):
        vessel = "10.1.0.%s" % self.leader_vessel
        print(data)
        self.contact_vessel(vessel, path, data)

    def send_message_to_neighbor(self, path, data):
        if('coordination' in data):
            print('Sending coordination message to ' + self.vessels[vessel_id % len(self.vessels)])
        else:
            print('Sending data message to ' + self.vessels[vessel_id % len(self.vessels)])
        thread = Thread(target=self.contact_vessel,
                        args=(self.vessels[vessel_id % len(self.vessels)], path, data))
        thread.daemon = True
        thread.start()

    def continue_election(self, instigator, leader, rank):
        print('Continue with election-process')
        thread = Thread(target=self.send_message_to_neighbor,
                        args=("/election",
                            {'instigator' : instigator,
                             'leader' : leader,
                             'rank'   : rank}))
        thread.daemon = True
        thread.start()
        #self.send_message_to_neighbor("/election",
        #                    {'instigator' : instigator,
        #                     'leader' : leader,
        #                     'rank'   : rank})

    def initiate_election(self):
        print("Starting election")
        sleep(2)
        self.continue_election(self.vessel_id, self.vessel_id, self.rank)
#------------------------------------------------------------------------------------------------------


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# This class implements the logic when a server receives a GET or POST request
# It can access to the server data through self.server.*
# i.e. the store is accessible through self.server.store
# Attributes of the server are SHARED accross all request hqndling/ threads!
class BlackboardRequestHandler(BaseHTTPRequestHandler):
#------------------------------------------------------------------------------------------------------
	# We fill the HTTP headers
    def set_HTTP_headers(self, status_code = 200):
		 # We set the response status code (200 if OK, something else otherwise)
		self.send_response(status_code)
		# We set the content type to HTML
		self.send_header("Content-type","text/html")
		# No more important headers, we can close them
		self.end_headers()
#------------------------------------------------------------------------------------------------------
	# a POST request must be parsed through urlparse.parse_QS, since the content is URL encoded
    def parse_POST_request(self):
		post_data = ""
		# We need to parse the response, so we must know the length of the content
		length = int(self.headers['Content-Length'])
		# we can now parse the content using parse_qs
		post_data = parse_qs(self.rfile.read(length), keep_blank_values=1)
		# we return the data
		return post_data
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Request handling - GET
#------------------------------------------------------------------------------------------------------
	# This function contains the logic executed when this server receives a GET request
	# This function is called AUTOMATICALLY upon reception and is executed as a thread!

    def do_GET(self):
    	print("Receiving a GET on path %s" % self.path)
    	# Here, we should check which path was requested and call the right logic based on it
        if(self.path == "/board" or self.path == "/"): #Fetch the entire HTML page
    	   self.do_GET_Index()
        elif(self.path == "/entries"): #Fetch only the entries of the board
           self.do_GET_entries()
        elif(self.path == "/entries/raw"): #Fetch only the entries of the board with no HTML
           self.do_GET_entries_raw()
        else: #Send 404 status to client if unknown path is requested
           self.set_HTTP_headers(404)
#------------------------------------------------------------------------------------------------------
# GET logic - specific path
#------------------------------------------------------------------------------------------------------
    def do_GET_entries(self):
        self.set_HTTP_headers(200)

        entryElems = ""

        #Loop through the list of all entries, create HTML element from
        #template for each. Add each of these to the entryElems string
        for (tag, entry) in self.server.store:
            entryElems += (entry_template % (("entries/" + str(tag)), tag , entry))

        #Return the generated HTML
        self.wfile.write(entryElems)

    #Get only the data of the entries in the blackboard with no HTML markup
    def do_GET_entries_raw(self):
        self.set_HTTP_headers(200)

        entryElems = []

        for (tag, entry) in self.server.store.iteritems():
            entryElems.append(entry)

    #    test = "<html><body>%s</body></html>"
        #Return the generated HTML
        self.wfile.write(entryElems)

    def do_GET_Index(self):
        # We set the response status code to 200 (OK)
        self.set_HTTP_headers(200)

        entryElems = ""

        #Loop through the list of all entries, create HTML element from
        #template for each. Add each of these to the entryElems string
        for (tag, entry) in self.server.store.iteritems():
            entryElems += (entry_template % (("entries/" + str(tag)), tag , entry))

        #Generate the body of the HTML from the template
        body = boardcontents_template % (BOARD_MESSAGE, entryElems)

        #Generate the footer from the template
        footer = board_frontpage_footer_template % (AUTHORS, str(self.server.rank))

        #Combine all HTML parts into a full page
        html_response = board_frontpage_header_template  + body + footer

        #Return the generated HTML page
        self.wfile.write(html_response)


#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------

    def do_POST(self):
        #Use different functions to handle POST requests depending on if there
        #is no leader elected yet and whether this vessel is the leader or not.
        if(self.server.leader_vessel == "" and (not self.server.leader)):
            print('Handle POST-request to elect leader')
            self.do_POST_no_leader()
        else:
            print('Handle POST-request')
            self.do_POST_leader()

    #Function used to handle POST requests before a leader has been elected.
    #Only requests regarding the election are accepted, all others receive
    #a status code 503, indicating that the blackboard is unavailable until
    #the election has been completed.
    def do_POST_no_leader(self):
        print("Receiving a POST on %s" % self.path)

        data = self.parse_POST_request()
        retransmit = False

        if(self.path == "/election"):
            try:
                if('coordination' in data):
                    #The request is a coordination message, intended to confirm
                    #the results of a concluded election
                    print("Coordination message received. Leader: " + data['leader'][0])
                    if(int(data['leader'][0]) == self.server.vessel_id):
                        #The coordination message sent by this vessel has gone
                        #around the ring and come back to it, indicating that it
                        #is free to assume leadership.
                        print(str(self.server.vessel_id) + " runs Barter Town")
                        self.server.leader = True
                    else:
                        #The vessel has received a coordination message from its
                        #neighbor, originally sent by the elected leader.
                        #Save the vessel_id of the leader and retransmit the
                        #coordination message to the next neighbor in the ring.
                        print(str(self.server.vessel_id) + " acknowledges that " +
                                data['leader'][0] + " runs Barter Town")
                        self.server.leader_vessel = data['leader'][0]
                        self.server.send_message_to_neighbor("/election", {'leader' : data['leader'][0],
                                                                           'coordination' : True})
                    self.set_HTTP_headers(200)
                else:
                    #The request indicates an active election
                    print("Election message received. Current leader: " + data['leader'][0])
                    if(int(data['instigator'][0]) == self.server.vessel_id):
                        #The election the request indicates was started by
                        #this vessel
                        if(int(data['leader'][0]) == self.server.vessel_id):
                            #This vessel has won the election.
                            #Send a coordination message to the neighbor
                            #to inform all other vessels of this.
                            print('We are instigator')
                            self.server.send_message_to_neighbor("/election",
                                                         {'coordination' : True,
                                                          'leader' : self.server.vessel_id})
                        else:
                            #This vessel has lost the election
                            print('We are not instigator any more')
                            #self.server.leader = data['leader'][0]
                    elif(int(data['rank'][0]) < self.server.rank):
                        #The election was started by another vessel and the
                        #current leader of the election has lower rank than
                        #this vessel. Change the values in the message to indicate
                        #that this vessel is the current leader of the election
                        #and send the message to the next neighbor.
                        print('Election: we have lower rank')
                        self.server.continue_election(data['instigator'][0],
                                                      self.server.vessel_id,
                                                      self.server.rank)
                    elif(int(data['rank'][0]) > self.server.rank):
                        #The election was started by another vessel and the
                        #current leader of the election has greater rank than
                        #this vessel. Send the message to the next neighbor
                        #withour change.
                        print('Election: we have higher rank -> self.leader')
                        self.server.continue_election(data['instigator'][0],
                                                      data['leader'][0],
                                                      data['rank'][0])
                    elif(int(data['leader'][0]) > self.server.vessel_id):
                    #The election was started by another vessel and the
                    #current leader of the election has equivalent rank
                    #to this vessel. Use the vessel_id of the current leader
                    #and this vessel as a tie breaker.
                        print('Election: same rank, tiebreaker won')
                        self.server.continue_election(data['instigator'][0],
                                                      self.server.vessel_id,
                                                      self.server.rank)
                    else:
                        print('Election: same, rank, tiebreaker lost')
                        self.server.continue_election(data['instigator'][0],
                                                      data['leader'][0],
                                                      data['rank'][0])
                    self.set_HTTP_headers(200)
            except Exception as e: #In case of any missing or malformed data,
                print(e)           #return error code
                self.set_HTTP_headers(400)
        else:
            self.set_HTTP_headers(503)

    def do_POST_leader(self):
        if self.server.t_0 == 0 and self.path != '/election':
            self.server.t_0 = time.time()
        print("Receiving a POST on %s" % self.path)
        # Here, we should check which path was requested and call the right logic based on it
        # We should also parse the data received
        # and set the headers for the client

        #Parse the data into a dictionary
        data = self.parse_POST_request()
        retransmit = False
        path       = "" #Variable to store path to propagate data to on other vessels
        propData   = {} #Dictionary to store propagation data. Values set
                        #depending on what type of request to propagate

        if(self.path == '/entries'):
        #Received a request to add a new post
            print("Recognized as new entry post")
            try:
                #Determine the key of the new entry
                #If this vessel is the leader, create new key
                #from current_key attribute in server
                #Otherwise, if message propagated from server, fetch key
                #from data
                #If message from client to non-leader vessel, set key to dummy value
                #Also, add new entry to local store only if this vessel is the leader
                #or if the message was propagated from the leader
                if self.server.leader:
                    nkey = self.server.add_value_to_store(data['entry'][0])
                elif 'sentFromLeader' in data:
                    print('Received post-request from leader')
                    nkey = int(data['key'][0])
                    print(nkey)
                    self.server.add_value_to_store(data['entry'][0], nkey)
                else:
                    nkey = None
                print(data['entry'][0])
                #The leader includes the assigned key of the new entry
                #in the propagation data, to ensure that all vessels
                #store the entry at the same key and ensure that values
                #are stored in the same order
                propData = {'entry' : data['entry'][0],
                            'key' : nkey}
                path     = '/entries'
                retransmit = True
                self.set_HTTP_headers(200)
            except Exception: #If some data is malformed or missing, return error code
                self.set_HTTP_headers(400)
        elif(self.server.current_key != 0 and
             re.match("/entries/[0-"+str(self.server.current_key -1)+"]", self.path)):
            #Received a request to either modify or delete a post
            print("Modify or delete post")
            try:
                if(data['delete'][0] == '1'):
                    print("Recognized as delete post")
                    if self.server.leader or 'sentFromLeader' in data:
                        self.server.delete_value_in_store(int(self.path.split("/")[2]))
                        print('Delete locally')
                    propData = {'delete' : '1', 'entry' : ''}
                else:
                    print("Recognized as modify post")
                    if self.server.leader or 'sentFromLeader' in data:
                        self.server.modify_value_in_store(int(self.path.split("/")[2]), data['entry'][0])
                        print('Modify locally')
                    propData = {'delete': '0', 'entry': data['entry'][0]}

                path = self.path
                retransmit = True
                self.set_HTTP_headers(200)
            except Exception: #If some data is malformed or missing, return error code
                self.set_HTTP_headers(400)
        else: #If request sent to unrecognized path, respond with error code 404
            self.set_HTTP_headers(404)

        # If the retransmit flag is set, call the propagation function.
        # Include the sentFromLeader flag to indicate to the other vessels that
        # the request is not sent from a client and that there is no need to
        # retransmit the request back to the leader.
        self.server.t_total = time.time()
        print("Diff:" + str(self.server.t_total - self.server.t_0))
        if retransmit and self.server.leader:
            print('Retransmit as leader')
            print(path)
            propData['sentFromLeader'] = True
            print(propData)
            self.server.propagate_value_to_vessels(path, propData)
        elif retransmit and not('sentFromLeader' in data):
            thread = Thread(target=self.server.contact_leader,
                            args=(path, propData))
            thread.daemon = True
            thread.start()


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Execute the code
if __name__ == '__main__':
    ## read the templates from the corresponding html files
    # .....

    vessel_id = 0
    vessel_list = []
    # Checking the arguments
    if len(sys.argv) != 3: # 2 args, the script and the vessel name
        print("Arguments: vessel_ID number_of_vessels")
    else:
        # We need to know the vessel IP
        vessel_id = int(sys.argv[1])
        #Generate a random rank for the vessel, used for leader election
        rank   = randint(0, 1000)
        print("RANK: " + str(rank))
        # We need to write the other vessels IP, based on the knowledge of their number

        for i in range(1, int(sys.argv[2])+1):
            vessel_list.append("10.1.0.%d" % i) # We can add ourselves, we have a test in the propagation


        board_frontpage_footer_template = open('server/board_frontpage_footer_template.html', 'rb').read()
        board_frontpage_header_template = open('server/board_frontpage_header_template.html', 'rb').read()
        boardcontents_template = open('server/boardcontents_template.html', 'rb').read()
        entry_template = open('server/entry_template.html', 'rb').read()

        # We launch a server
        server = BlackboardServer(('', PORT_NUMBER), BlackboardRequestHandler, vessel_id, vessel_list, rank)
        print("Starting the server on port %d" % PORT_NUMBER)

        thread = Thread(target=server.initiate_election,args=() )
        # We kill the process if we kill the server
        thread.daemon = True
        # We start the thread
        thread.start()

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
            print("Stopping Server")
#------------------------------------------------------------------------------------------------------

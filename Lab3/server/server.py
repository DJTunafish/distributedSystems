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

# Used to compare
import functools
#------------------------------------------------------------------------------------------------------

# Global variables for HTML templates
board_frontpage_footer_template = ""
board_frontpage_header_template = ""
boardcontents_template = ""
entry_template = ""

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
    def __init__(self, server_address, handler, node_id, vessel_list):
        # We call the super init
        HTTPServer.__init__(self,server_address, handler)
        # we create the dictionary of values
        self.store = {}
        # We keep a variable of the next id to insert
        self.logical_clock = 0
        # our own ID (IP is 10.1.0.ID)
        self.vessel_id = vessel_id
        # The list of other vessels
        self.vessels = vessel_list
        # History of modification of entries
        self.modHistory = {}
        # List of messages that are dependent on messages that have yet to arrive
        self.messageQueue = []
#------------------------------------------------------------------------------------------------------

    def check_queue(self, key):
        # Need to have a removeList, because Python stops loop after concurrent remove
        # There might be more than 1 msg for this post in the queue
        removeList = []
        for msg in self.messageQueue:
            if msg[1] == key:
                # modify
                if msg[0] == 0:
                    self.modify_value_in_store(msg[1], msg[2], msg[3], msg[4])
                # delete
                else:
                    self.delete_value_in_store(msg[1])
                removeList.append(msg)

        for msg in removeList:
            self.messageQueue.remove(msg)


    # We add a value received to the store
    #value: value to be added to the store
    #Adds a value to the store
    #Returns key of the value
    def add_value_to_store(self, value, key=None):
        # We add the value to the store
        if key == None:
            key = str(self.logical_clock + 1) + '-' + str(self.vessel_id)

        self.store[key]      = value
        self.modHistory[key] = None
        self.check_queue(key)
        return key
#------------------------------------------------------------------------------------------------------
    # We modify a value received in the store, if the key exists
    # key   = key of the value to modify
    # value = new value
    def modify_value_in_store(self,key,value,modifying_vessel_clock=None,
                              modifying_vessel_id=None):
        if key in self.store and (self.modHistory[key] == None or
           self.modHistory[key][0] < modifying_vessel_clock or
           (self.modHistory[key][0] == modifying_vessel_clock and
           self.modHistory[key][1] < modifying_vessel_id)):

            self.store[key] = value
            self.modHistory[key] = [modifying_vessel_clock, modifying_vessel_id]
        elif not(key in self.store):
            # 0 = modify
            # 1 = delete
            self.messageQueue.append([0, key, value, modifying_vessel_clock, modifying_vessel_id])
#------------------------------------------------------------------------------------------------------
    # We delete a value received from the store, if it exists in the store
    # key = key of value to delete
    def delete_value_in_store(self,key):
        if(key in self.store):
            self.store.pop(key, None)
        else:
            self.messageQueue.append([1, key])
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
        data['propagate'] = '1'
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
            print "Error while contacting %s" % vessel_ip
            # printing the error given by Python
            print(e)

        # we return if we succeeded or not
        return success
#------------------------------------------------------------------------------------------------------
    # We send a received value to all the other vessels of the system, via HTTP
    # POST requests
    # path = path to send the POST request to
    # data = dictionary of vaues to include in the POST requests
    def propagate_value_to_vessels(self, path, data):
        print("Propagation time!")
        # We iterate through the vessel list
        for vessel in self.vessels:
            print(vessel)
            # We should not send it to our own IP, or we would create an infinite loop of updates
            if vessel != ("10.1.0.%s" % self.vessel_id):
                # A good practice would be to try again if the request failed
                # Here, we do it only once
                self.contact_vessel(vessel, path, data)
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
        else: #Send 404 status to client if unknown path is requested
           self.set_HTTP_headers(404)
#------------------------------------------------------------------------------------------------------
# GET logic - specific path
#------------------------------------------------------------------------------------------------------
    #TODO: Write as lambda
    def compareMsgId(instance_ref, item1, item2):
        tmp1 = item1[0].split('-')
        tmp2 = item2[0].split('-')
        print('------- comparison -------')
        print(tmp1[0] + ' ' + tmp1[1])
        print(tmp2[0] + ' ' + tmp2[1])

        if int(tmp1[0]) != int(tmp2[0]):
            return int(tmp1[0]) < int(tmp2[0])
        else:
            return int(tmp1[1]) < int(tmp2[1])


    def do_GET_entries(self):
        self.set_HTTP_headers(200)

        entryElems = ""

        #Loop through the list of all entries, create HTML element from
        #template for each. Add each of these to the entryElems string
        for (tag, entry) in sorted(self.server.store.iteritems(), cmp=self.compareMsgId):
            entryElems += (entry_template % (("entries/" + str(tag)), tag , entry))

        #Return the generated HTML
        self.wfile.write(entryElems)

    def do_GET_Index(self):
        # We set the response status code to 200 (OK)
        self.set_HTTP_headers(200)

        entryElems = ""

        #Loop through the list of all entries, create HTML element from
        #template for each. Add each of these to the entryElems string
        for (tag, entry) in sorted(self.server.store.iteritems(), cmp=self.compareMsgId):
            entryElems += (entry_template % (("entries/" + str(tag)), tag , entry))

        #Generate the body of the HTML from the template
        body = boardcontents_template % (BOARD_MESSAGE, entryElems)

        #Generate the footer from the template
        footer = board_frontpage_footer_template % AUTHORS

        #Combine all HTML parts into a full page
        html_response = board_frontpage_header_template + body + footer

        #Return the generated HTML page
        self.wfile.write(html_response)


#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------
    def do_POST(self):
        print("Receiving a POST on %s" % self.path)
        # Here, we should check which path was requested and call the right logic based on it
        # We should also parse the data received
        # and set the headers for the client

        #Parse the data into a dictionary

        data = self.parse_POST_request()
        print(data)

        if('clock' in data and int(data['clock'][0] > self.server.logical_clock)):
            self.server.logical_clock = int(data['clock'][0]) + 1
        else:
            self.server.logical_clock += 1

        retransmit = False
        path       = "" #Variable to store path to propagate data to on other vessels
        propData   = {'clock'  : self.server.logical_clock + 1,
                      'sender' : self.server.vessel_id} #Dictionary to store propagation data. Values set
                        #depending on what type of request to propagate

        if(self.path == '/entries'):
        #Received a request to add a new post
            print("Recognized as new entry post")
            try:
                key = None
                #Check if this is a post received from another server
                if('clock' in data):
                    print('got in here - clock in data test')
                    key = data['clock'][0] + '-' + data['sender'][0]
                print('Adding value to store')
                self.server.add_value_to_store(data['entry'][0], key)
                print('Adding done')
                propData['entry'] = data['entry'][0]
                path     = '/entries'
                retransmit = True
                print("Retransmit set")
                self.set_HTTP_headers(200)
            except Exception as e: #If some data is malformed or missing, return error code
                print(e)
                self.set_HTTP_headers(400)
        elif(self.server.logical_clock != 0 and
             re.match("/entries/[0-"+str(self.server.logical_clock -1)+"]", self.path)):
            #Received a request to either modify or delete a post
            try:
                if(data['delete'][0] == '1'):
                    print("Recognized as delete post")
                    self.server.delete_value_in_store(int(self.path.split("/")[2]))
                    propData['delete'] = '1'
                    propData['entry']  = ''
                else:
                    print("Recognized as modify post")
                    if('clock' in data):
                        self.server.modify_value_in_store(int(self.path.split("/")[2]),
                                                          data['entry'][0],
                                                          int(data['clock'][0]),
                                                          int(data['sender'][0]))
                    else:
                        self.server.modify_value_in_store(int(self.path.split("/")[2]),
                                                          data['entry'][0])
                    propData['delete'] = '0'
                    propData['entry']  = data['entry'][0]

                path = self.path
                retransmit = True
                self.set_HTTP_headers(200)
            except Exception: #If some data is malformed or missing, return error code
                self.set_HTTP_headers(400)
        else: #If request sent to unrecognized path, respond with error code 404
            self.set_HTTP_headers(404)

        # If the retransmit flag is set, call the propagation function, but only
        # if the propagate flag is not set in the received data. This latter flag
        # indicates that the POST request was sent from another vessel and should
        # not be propagated by this vessel
        print("Transmit condition: " + str(retransmit and not('clock' in data)))
        print(retransmit)
        print(data)
        if retransmit and not('clock' in data):
            # do_POST send the message only when the function finishes
            # We must then create threads if we want to do some heavy computation
            #
            # Random content
            print("Retransmitting")
            self.server.logical_clock += 1
            thread = Thread(target=self.server.propagate_value_to_vessels,args=(path, propData) )
            # We kill the process if we kill the server
            thread.daemon = True
            # We start the thread
            thread.start()

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Execute the code
if __name__ == '__main__':
    ## read the templates from the corresponding html files
    # .....

    vessel_list = []
    vessel_id = 0
    # Checking the arguments
    if len(sys.argv) != 3: # 2 args, the script and the vessel name
        print("Arguments: vessel_ID number_of_vessels")
    else:
        # We need to know the vessel IP
        vessel_id = int(sys.argv[1])
        # We need to write the other vessels IP, based on the knowledge of their number
        for i in range(1, int(sys.argv[2])+1):
            vessel_list.append("10.1.0.%d" % i) # We can add ourselves, we have a test in the propagation

        board_frontpage_footer_template = open('server/board_frontpage_footer_template.html', 'rb').read()
        board_frontpage_header_template = open('server/board_frontpage_header_template.html', 'rb').read()
        boardcontents_template = open('server/boardcontents_template.html', 'rb').read()
        entry_template = open('server/entry_template.html', 'rb').read()

        # We launch a server
        server = BlackboardServer(('', PORT_NUMBER), BlackboardRequestHandler, vessel_id, vessel_list)
        print("Starting the server on port %d" % PORT_NUMBER)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
            print("Stopping Server")
#------------------------------------------------------------------------------------------------------

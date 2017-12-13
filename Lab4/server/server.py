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
from sets import Set
from byzantine_behavior import compute_byzantine_vote_round1, compute_byzantine_vote_round2
import functools
#------------------------------------------------------------------------------------------------------

# Global variables for HTML templates
voting_template = ""
vote_result_template = ""

AUTHORS = "Erik Jungmark & Patrick Franz"

#------------------------------------------------------------------------------------------------------
# Static variables definitions
PORT_NUMBER = 80
#------------------------------------------------------------------------------------------------------



#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class ByzantineServer(HTTPServer):
    #------------------------------------------------------------------------------------------------------
    def __init__(self, server_address, handler, node_id, vessel_list, byzantineAmount):
        # We call the super init
        HTTPServer.__init__(self,server_address, handler)
        # we create the dictionary of values
        # our own ID (IP is 10.1.0.ID)
        self.vessel_id = vessel_id
        # The list of other vessels
        self.vessels = vessel_list
        #Number of byzantine servers present
        self.byzantineServers = byzantineAmount
        #Votes received from other nodes this round
        self.receivedVotes = {}
        #Result vectors received this round
        self.receivedResultVectors = {}
        #Result of latest voting round
        self.result = None
        self.byzantine = False
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
        # We iterate through the vessel list
        for vessel in self.vessels:
            # We should not send it to our own IP, or we would create an infinite loop of updates
            if vessel != ("10.1.0.%s" % self.vessel_id):
                # A good practice would be to try again if the request failed
                # Here, we do it only once
                thread = Thread(target=self.contact_vessel,args=(vessel, path, data))
                thread.daemon = True
                thread.start()

    #Value propagation for a byzantine server. The dataSets parameter should
    #contain a list of different data to propagate to different servers, as
    #a byzantine server may send different data to different server.
    #Sends the first value to the first server, the second value to the second server, etc
    def propagate_byzantine(self, path, dataSets):
        i = 0
        print(self.vessels)
        for vessel in self.vessels:
            if vessel != ("10.1.0.%s" % self.vessel_id):
                thread = Thread(target=self.contact_vessel,args=(vessel, path, dataSets[i]))
                thread.daemon = True
                thread.start()
                i += 1
#------------------------------------------------------------------------------------------------------


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# This class implements the logic when a server receives a GET or POST request
# It can access to the server data through self.server.*
# i.e. the store is accessible through self.server.store
# Attributes of the server are SHARED accross all request hqndling/ threads!
class ByzantineRequestHandler(BaseHTTPRequestHandler):
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
        if self.path == "/": #Get the basic page
            self.wfile.write(voting_template)
            self.set_HTTP_headers(200)
        elif self.path == "/vote/result":
            #Fetch HTML representing the result
            #of the latest round of voting
#TODO: Show result vector here
            result = ""
            if self.server.result == None:
                result = "None"
            else:
                result = self.server.result

            vote = ""
            if self.server.vessel_id in self.server.receivedVotes:
                vote = self.server.receivedVotes[self.server.vessel_id]
            else:
                vote = "No vote cast"

            html = vote_result_template % (result, vote)

            self.wfile.write(html)
        else:
            print("Unrecognized get request")
            self.set_HTTP_headers(500)

#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------
    def do_POST(self):
        data = self.parse_POST_request()

        if self.path == "/voteRound2":
            print("Result vector received")
            print(data)
            #The POST request is from another server that is sending its
            #result vector
            self.parse_result_vector(data)

            if len(self.server.receivedResultVectors) == (len(self.server.vessels)):
                #Result vectors from all other servers have been received,
                #compute the final result
                self.compute_round_2()
        elif 'generalVote' in data:
            print("Vote received")
            print(data)
            #The POST request is from another server that is sending its vote
            self.receive_vote(data)

            print(len(self.server.receivedVotes))
            if len(self.server.receivedVotes) == len(self.server.vessels):
                #Votes from all servers have been received, calculate result
                #and send out result vector to all other servers
                self.compute_round_1()

                if len(self.server.receivedResultVectors) == (len(self.server.vessels)):
                    #Result vectors from all other servers have been received,
                    #compute the final result
                    self.compute_round_2()
        else:
            print("Casting vote")
            #The POST request came from a client instructing the server
            #to cast its vote
            self.vote()

            if len(self.server.receivedVotes) == len(self.server.vessels):
                #Votes from all servers have been received, calculate result
                #and send out result vector to all other servers
                self.compute_round_1()


    def compute_round_1(self):
        print("Compute round 1 result")
        if self.server.byzantine:
            #This server should act in a byzantine manner
            vectors = compute_byzantine_vote_round2(len(self.server.vessels) - self.server.byzantineServers,
                                                    len(self.server.vessels), True)

            dicts = []
            for vect in vectors:
                dictX = {}
                for i in range(1, len(self.server.vessels) + 1):
                    dictX[i] = vect[i - 1]
                dictX['sender'] = self.server.vessel_id
                dicts.append(dictX)
            #TODO: Something else as tiebreaker?
            self.server.receivedResultVectors[self.server.vessel_id] = dicts[0]
            self.server.propagate_byzantine("/voteRound2", dicts)
        else:
            #resultVector = []
            #print("Received votes:")
            #print(self.server.receivedVotes)
            #for (key, val) in sorted(self.server.receivedVotes.iteritems()):
            #    resultVector.append(val)
            print("Result vector:")
            print(self.server.receivedVotes)
            resultVector = dict(self.server.receivedVotes)
            resultVector['sender'] = self.server.vessel_id

            resultVectorList = []
            for (key, val) in sorted(resultVector.iteritems()):
                if(key != 'sender'):
                    resultVectorList.append(val)

            self.server.receivedResultVectors[self.server.vessel_id] = resultVectorList
            self.server.propagate_value_to_vessels("/voteRound2", resultVector)

    def compute_round_2(self):
        finalVector = []
        #Iterate through every index in the resultVectors.
        #For a given index i, check the entries at that index for every
        #result vector, counting the amount of votes for retreat and the votes
        #for attack. If there is a majority of votes for either choice, append
        #this result to the final result vector. Otherwise, append None to the
        #final vector, indicating that the result is undecidable.
        print("Compute round 2 result")
        finalAttackVotes = 0
        finalRetreatVotes = 0

        for i in range(1, len(self.server.vessels) + 1):
            print("Compute value " + str(i))
            if i == self.server.vessel_id:
                print("Appending own value")
                finalVector.append(self.server.receivedVotes[self.server.vessel_id])
            else:
                retreatVotes = 0
                attackVotes  = 0

                for (vessel, vector) in self.server.receivedResultVectors.iteritems():
                    vectorEntry = vector[i-1]
                    if vessel != i and vectorEntry:
                        attackVotes += 1
                    elif vessel != i:
                        retreatVotes += 1
                    else:
                        print("For value " + str(i) + ", skipped vote of " + str(vessel))

                if attackVotes > retreatVotes:
                    finalVector.append(True)
                    finalAttackVotes += 1
                elif retreatVotes > attackVotes:
                    finalVector.append(False)
                    finalRetreatVotes += 1
                else:
                    finalVector.append(None)

        print("Final vector: " + str(finalVector))
        print("Final attack votes: " + str(finalAttackVotes) )
        print("Final retreat votes: " + str(finalRetreatVotes) )

        self.server.finalResultVector = finalVector
        if finalAttackVotes > finalRetreatVotes:
            self.server.result = 'Attack!'
            print("CHAAAARGE!")
        else:
            self.server.result = 'Retreat!'
            print("RUN AWAY!")

        self.server.receivedVotes = {}
        self.server.receivedResultVectors = {}


    #Parse a result vector from a list of strings to a list of boolean values
    #and store the result
    def parse_result_vector(self, vector):
        if not (int(vector['sender'][0]) in self.server.receivedResultVectors):
            self.set_HTTP_headers(200)
            parsedVector = []
            print("Received vector: ")
            print(vector)
            for (key, val) in sorted(vector.iteritems()):
                if(key != 'sender'):
                    parsedVector.append(val[0] == 'True')
            print("Parsed vector: " )
            print(parsedVector)
            self.server.receivedResultVectors[int(vector['sender'][0])] = parsedVector

    #Vote based on the path used for the request and propagate this decision
    #to all other servers
    def vote(self):
        if self.path == "/vote/attack":
            self.server.byzantine = False
            print("Voting attack")
            self.server.propagate_value_to_vessels('/vote', {'generalVote' : True,
                                                             'sender'      : self.server.vessel_id})
            self.server.receivedVotes[self.server.vessel_id] = 'True'

        elif self.path == "/vote/retreat":
            print("Voting retreat")
            self.server.byzantine = False
            self.server.propagate_value_to_vessels('/vote', {'generalVote' : False,
                                                             'sender' : self.server.vessel_id})
            self.server.receivedVotes[self.server.vessel_id] = 'False'
        elif self.path == "/vote/byzantine":
            print("Voting byzantine")
            self.server.byzantine = True
            votes = compute_byzantine_vote_round1(len(self.server.vessels) - self.server.byzantineServers,
                                                  len(self.server.vessels), True)
            #TODO: Set tie-breaker to something fancy?
            propData = []
            for vote in votes:
                d = {'generalVote' : vote,
                     'sender'      : self.server.vessel_id}
                propData.append(d)

            self.server.receivedVotes[self.server.vessel_id] = 'Byzantine'
            self.server.propagate_byzantine('/vote', propData)
        else:
            print("Non-acceptable URL for client vote")
            self.set_HTTP_headers(500)

    #Receive a vote from another server
    def receive_vote(self, data):
        if self.path == "/vote":
            print("Receive vote")
            self.set_HTTP_headers(200)
            if int(data['sender'][0]) not in self.server.receivedVotes:
                print("Add received vote to store")
                self.server.receivedVotes[int(data['sender'][0])] = data['generalVote'][0]
        else:
            print("Vote sent to incorrect URL")
            self.set_HTTP_headers(500)

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Execute the code
if __name__ == '__main__':
    ## read the templates from the corresponding html files
    # .....

    vessel_list = []
    vessel_id = 0
    # Checking the arguments
    if len(sys.argv) != 4: # 2 args, the script and the vessel name
        print("Arguments: vessel_ID number_of_vessels number_of_byzantine")
    else:
        # We need to know the vessel IP
        vessel_id = int(sys.argv[1])
        # We need to write the other vessels IP, based on the knowledge of their number
        for i in range(1, int(sys.argv[2])+1):
            vessel_list.append("10.1.0.%d" % i) # We can add ourselves, we have a test in the propagation

        voting_template = open('server/vote_frontpage_template.html', 'rb').read()
        vote_result_template = open('server/vote_result_template.html', 'rb').read()

        # We launch a server
        server = ByzantineServer(('', PORT_NUMBER), ByzantineRequestHandler, vessel_id, vessel_list, int(sys.argv[3]))
        print("Starting the server on port %d" % PORT_NUMBER)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
            print("Stopping Server")
#------------------------------------------------------------------------------------------------------

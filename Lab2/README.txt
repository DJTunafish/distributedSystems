---------------------------------------
File descriptions
---------------------------------------
testScript.sh: Script for testing the servers
API-description.txt: Description of the routes used in the server
Report.txt: Contains reports for all tasks, including cost analyses


-----------------------------------
Unit test script:
-----------------------------------
Unit tests located in testScript2.sh.
To run tests, start up the lab1.py mininet topology, then run
testScript2.sh from any client.
The unit test will automatically check that all vessels are consistent.
There is some error with the prints in the script such that it always prints
"Vessel X and vessel 1 are consistent", but we have checked that the script
does actually compare all vessels. 

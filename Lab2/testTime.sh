#!/bin/bash
if [ $# -ne 2 ]
then
	echo "Need 2 arguments - 1. number of servers 2. number of requests per server"
	exit 1
fi

no_servers=$1
no_requests=$2
echo "Sending requests ..."
for i in `seq 1 ${no_requests}`; do
	echo "Sending request no. ${i}"
	for j in `seq 1 ${no_servers}`; do
		SERVER=$((j))
		IPPREFIX="10.1.0."
		IPSUFFIX="/entries"
		IP=${IPPREFIX}${SERVER}${IPSUFFIX}
		curl -s --data 'entry=test'${i} -X POST ${IP}
	done
done
echo "Done."

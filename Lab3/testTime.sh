#!/bin/bash
if [ $# -ne 1 ]
then
	echo "Need 1 argument - number of servers"
	exit 1
fi

no_servers=$1
for i in `seq 1 ${no_servers}`; do
	SERVER=$((i))
	IPPREFIX="10.1.0."
	IPSUFFIX="/entries"
	IP=${IPPREFIX}${SERVER}${IPSUFFIX}
	echo "Sending requests to server ${SERVER} ..."
	for j in `seq 1 40`; do
			curl -s --data 'entry=test'${i} -X POST ${IP}
	done
done

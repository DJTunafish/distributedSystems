#!/bin/bash
if [ $# -ne 1 ]; then
	echo "Need 1 argument - number of servers"
	exit 1
fi

no_servers=$(($1-1))
test_fail=false

for i in `seq 1 ${no_servers}`; do
	j=$((i+1))
	IPPREFIX="10.1.0."
	IPSUFFIX="/entries/raw"
	FSTIP=${IPPREFIX}${i}${IPSUFFIX}
	SNDIP=${IPPREFIX}${j}${IPSUFFIX}
	FSTRES=$(curl -s -X GET ${FSTIP})
	SNDRES=$(curl -s -X GET ${SNDIP})
	if [ "$FSTRES" != "$SNDRES" ]; then
		echo "Vessel $i and vessel $j are not consistent"
		test_fail=true
	fi
done

if [ "$test_fail" = false ]; then
	echo "All vessels are consistent"
fi

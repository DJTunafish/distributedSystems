#!/bin/bash
for i in `seq 1 20`; do
	RANDOMNR="$(( ( RANDOM % 10 )  + 1 ))"
    ACTION="$(( ( RANDOM % 3 )  + 1 ))"
	IPPREFIX="10.1.0."
	IPSUFFIX="/entries"
	RANDOMIP=${IPPREFIX}${RANDOMNR}${IPSUFFIX}
	curl -s --data 'entry=test'${i} -X POST ${RANDOMIP}
done

sleep 2

for i in `seq 1 9`; do
	j=$((i+1))
	IPPREFIX="10.1.0."
	IPSUFFIX="/entries/raw"
	FSTIP=${IPPREFIX}${i}${IPSUFFIX}
	SNDIP=${IPPREFIX}${j}${IPSUFFIX}
	FSTRES=$(curl -s -X GET ${FSTIP})
	SNDRES=$(curl -s -X GET ${SNDIP})
	if [ "$FSTRES" == "$SNDRES" ]; then
		 echo "Vessel $i and vessel $j are consistent"
	else
		echo "Vessel $i and vessel $j are not consistent"
	fi
done

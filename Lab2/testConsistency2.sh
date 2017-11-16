#!/bin/zsh
for i in `seq 1 20`; do
	RANDOMNR="$(( ( RANDOM % 10 )  + 1 ))"
	IPPREFIX="10.1.0."
	IPSUFFIX="/entries"
	RANDOMIP=${IPPREFIX}${RANDOMNR}${IPSUFFIX}
	curl -s --data 'entry=test'${i} -X POST ${RANDOMIP}
done

sleep 2

for i in `seq 1 9`; do
	IPPREFIX="10.1.0."
	IPSUFFIX="/entries/raw"
	FSTIP=${IPPREFIX}${i}${IPSUFFIX}
    SNDIP=${IPPREFIX}${i+1}${IPSUFFIX}
	FSTRES=$(curl -s -X GET ${FSTIP})
    SNDRES=$(curl -s -X GET ${SNDIP})
    DIFF=$(diff  <(echo "$FSTRES" ) <(echo "$SNDRES"))
    if ["$DIFF" != ""]; then
         echo "Vessel $i and vessel ${i+1} are not consistent"
    fi
done

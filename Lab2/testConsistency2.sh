#!/bin/zsh
for i in `seq 1 20`; do
	RANDOMNR="$(( ( RANDOM % 10 )  + 1 ))"
	IPPREFIX="10.1.0."
	IPSUFFIX="/entries"
	RANDOMIP=${IPPREFIX}${RANDOMNR}${IPSUFFIX}
	curl -s --data 'entry=test'${i} -X POST ${RANDOMIP}
done


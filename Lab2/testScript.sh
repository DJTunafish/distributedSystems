#!/bin/bash
sleep 3
curl -v -X POST 10.1.0.1/entries --data "entry=test1"
sleep 5
curl -v -X POST 10.1.0.8/entries --data "entry=test2"
sleep 5
curl -v -X POST 10.1.0.6/entries/1 --data "entry=test3&delete=0"
sleep 7
curl -v -X POST 10.1.0.5/entries/1 --data "entry=test3&delete=1"
curl -v -X POST 10.1.0.4/entries/0 --data "entry=test4&delete=0"
sleep 5
curl -v -X POST 10.1.0.7/entries --data "entry=test5" &
curl -v -X POST 10.1.0.9/entries --data "entry=test6" &
curl -v -X POST 10.1.0.2/entries --data "entry=test7" &
curl -v -X POST 10.1.0.3/entries --data "entry=test8"

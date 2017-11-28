#!/bin/zsh
curl -s -X POST 10.1.0.7/entries --data "entry=test1"
curl -s -X POST 10.1.0.6/entries --data "entry=test2"
curl -s -X POST 10.1.0.5/entries --data "entry=test3"
curl -s -X POST 10.1.0.4/entries --data "entry=test4"
curl -s -X POST 10.1.0.1/entries --data "entry=test5"
curl -s -X POST 10.1.0.9/entries --data "entry=test6"
curl -s -X POST 10.1.0.2/entries --data "entry=test7"
curl -s -X POST 10.1.0.3/entries --data "entry=test8"

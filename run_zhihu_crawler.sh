#!/bin/bash
while true
do 
    python2 zh_crawler.py
    if [ "$?" -ne 0 ] ;
        then exit -1;
    fi;
done;
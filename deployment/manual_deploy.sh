#!/usr/bin/env bash

pwd

docker rm -f $(docker ps -aq -f "network=traintravellers")

docker ps -a

docker build Audit/ -t audit:vt

docker build Receiver/ -t receiver:vt

docker build Processing/ -t processing:vt

docker build Storage/ -t storage:vt

docker build Dashboard-UI/ -t dashboard:vt

docker network create traintravellers

docker run -d --name receiver --hostname receiver --network traintravellers -p 8080:8080 receiver:vt

docker run -d --name storage --hostname storage --network traintravellers -p 8090:8090 storage:vt

docker run -d --name processing --hostname processing --network traintravellers -p 8100:8100 processing:vt

docker run -d --name audit --hostname processing --network traintravellers -p 9010:9010 audit:vt

docker run -d --name dashboard --hostname dashboard --network traintravellers -p 3000:3000 dashboard:vt


docker ps -a

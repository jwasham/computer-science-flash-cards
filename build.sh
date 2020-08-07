#!/bin/bash

docker stop cs-flash-cards
docker rm cs-flash-cards
docker build . -t cs-flash-cards
docker run -d -p 8000:8000 --name cs-flash-cards -v `pwd`/db:/src/db cs-flash-cards

#!/bin/bash
set -ex
cd ${0%/*}
cd ..
rm -f docker/app.tar
cp requirements.txt docker/requirements.txt
tar --exclude docker -cvf  docker/app.tar * ||true
cd docker
docker compose -f $1 build
docker compose -f $1 push
#!/bin/bash
set -e
cd ${0%/*}
./build.sh $1
./run.sh $1
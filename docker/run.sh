#!/bin/bash
set -e
cd ${0%/*}
docker compose -f $1 up -d
docker compose -f $1 logs -f
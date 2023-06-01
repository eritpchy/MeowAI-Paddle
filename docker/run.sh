#!/bin/bash
set -e
cd ${0%/*}
docker compose up -d
docker compose logs -f
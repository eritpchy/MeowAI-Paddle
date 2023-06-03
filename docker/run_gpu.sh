#!/bin/bash
set -e
cd ${0%/*}
docker compose -f gpu.yml up -d
docker compose -f gpu.yml logs -f
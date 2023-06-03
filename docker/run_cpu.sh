#!/bin/bash
set -e
cd ${0%/*}
docker compose -f cpu.yml up -d
docker compose -f cpu.yml logs -f
#!/bin/bash
set -e
cd ${0%/*}
./build_gpu.sh
./run_gpu.sh
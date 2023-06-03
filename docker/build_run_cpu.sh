#!/bin/bash
set -e
cd ${0%/*}
./build_cpu.sh
./run_cpu.sh
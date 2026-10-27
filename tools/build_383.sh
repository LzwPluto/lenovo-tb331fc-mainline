#!/bin/bash
set -e
cd /mnt/d/TB331FCLinux
python3 tools/make_383_dts.py
cd build

dtc -@ -I dts -O dtb -o CANONICAL_383.dtb CANONICAL_383.dts 2>&1 | grep -E 'ERROR|FATAL' | head -3 || true
ls -l CANONICAL_383.dtb

echo "--- DPU opp-table ---"
dtc -I dtb -O dts CANONICAL_383.dtb 2>/dev/null \
  | awk '/phandle = <0x72>;/{f=1} f{print} f&&/^\t\t\t\t};/{exit}' \
  | grep -E 'opp-|opp-hz'

echo "--- symbols count ---"
dtc -I dtb -O dts CANONICAL_383.dtb 2>/dev/null \
  | sed -n '/__symbols__ {/,/};/p' | grep -c '= "'

#!/bin/bash
cd /mnt/d/TB331FCLinux/build || exit 1
F=CANONICAL_oppfix.dts

echo "=== __symbols__ present? ==="
grep -c '__symbols__' "$F"

echo "=== symbol count (approx) ==="
sed -n '/__symbols__ {/,/};/p' "$F" | grep -c '= "'

echo "=== bootargs lines ==="
grep -n 'bootargs' "$F" | head -4

echo "=== DPU opp-table (phandle 0x72) ==="
awk '/phandle = <0x72>;/{f=1} f{print} f&&/^\t\t\t\t};/{exit}' "$F" | head -40

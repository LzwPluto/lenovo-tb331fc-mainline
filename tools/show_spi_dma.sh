#!/bin/bash
cd /mnt/d/TB331FCLinux/build || exit 1
F=CANONICAL_383.dts

echo "=== spi@4a80000 node ==="
awk '/spi@4a80000 \{/{f=1} f{print} f&&/^\t\t\t\};/{exit}' "$F" | head -25

echo
echo "=== a neighbouring geni node that still has dmas ==="
grep -n 'dmas =' "$F" | head -6
echo
echo "=== example with context ==="
N=$(grep -n 'dmas =' "$F" | head -1 | cut -d: -f1)
if [ -n "$N" ]; then
    sed -n "$((N-6)),$((N+3))p" "$F"
fi

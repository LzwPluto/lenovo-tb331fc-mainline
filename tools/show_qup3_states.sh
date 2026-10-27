#!/bin/bash
set +e
D=/mnt/d/TB331FCLinux/build/CANONICAL.dts
echo "=== all pin states mentioning gpio8 / qup3 ==="
grep -n -B4 -A6 'function = "qup3"' "$D" | head -60

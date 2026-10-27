#!/bin/bash
set +e
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts
echo "=== vendor node at 4a8c000 ==="
grep -n "4a8c000" "$V" | head -8
echo
ln=$(grep -n "4a8c000" "$V" | grep -v aliases | head -1 | cut -d: -f1)
echo "--- context around line $ln ---"
sed -n "$((ln-2)),$((ln+24))p" "$V"

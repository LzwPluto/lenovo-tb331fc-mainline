#!/bin/bash
set +e
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts

echo "=== VENDOR: IPCRTR occurrences ==="
grep -n "IPCRTR" "$V" | head -12

echo
echo "=== VENDOR: context of first IPCRTR ==="
ln=$(grep -n "IPCRTR" "$V" | head -1 | cut -d: -f1)
if [ -n "$ln" ]; then
    start=$((ln-10)); [ $start -lt 1 ] && start=1
    sed -n "${start},$((ln+6))p" "$V"
fi

echo
echo "=== OUR dts: IPCRTR / glink-channels / smd-edge ==="
grep -n "IPCRTR\|glink-channels\|smd-edge\|qcom,glink" "$C" | head -12

echo
echo "=== VENDOR: all glink-channels ==="
grep -n 'qcom,glink-channels' "$V" | head -12

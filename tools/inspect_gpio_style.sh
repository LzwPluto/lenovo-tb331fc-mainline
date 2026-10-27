#!/bin/bash
cd /mnt/d/TB331FCLinux/build || exit 1

echo "=== phandle of pinctrl@500000 (the real tlmm) ==="
awk 'NR>=830 && NR<=900 && /phandle/ {print NR": "$0}' CANONICAL_383_dma.dts | head -5
sed -n '830,900p' CANONICAL_383_dma.dts | grep -n 'phandle'

echo
echo "=== touchscreen@1 node (GPIO reference style) ==="
grep -n -A20 'touchscreen@1' CANONICAL_383_dma.dts | head -26

echo
echo "=== a fixed regulator without a gpio (always-on style) ==="
grep -n -B2 -A8 'regulator-always-on' CANONICAL_383_dma.dts | head -20

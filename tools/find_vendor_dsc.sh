#!/bin/bash
cd /mnt/d/TB331FCLinux || exit 1

echo "=== files containing compression-mode ==="
grep -rl 'compression-mode' build/*.dts stock_dtbo_entries/*.dts 2>/dev/null | head -10

F=$(grep -rl 'compression-mode' build/*.dts stock_dtbo_entries/*.dts 2>/dev/null | head -1)
echo
echo "file = $F"
if [ -n "$F" ]; then
    echo "=== DSC properties ==="
    grep -nE 'compression-mode|mdss-dsc|slice|bits-per' "$F" | head -30
    echo
    echo "=== panel timing / clockrate ==="
    grep -nE 'panel-width|panel-height|panel-framerate|panel-clockrate|dsi-(h|v)(fp|bp|pw)-value' "$F" | head -20
fi

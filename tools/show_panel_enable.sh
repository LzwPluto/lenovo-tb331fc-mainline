#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
F=drivers/gpu/drm/panel/panel-himax-hx83102.c

echo "=== enable function ==="
awk '/static int hx83102_enable\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$F" | head -60

echo
echo "=== any gpio / reset handling in the driver ==="
grep -n "gpio\|reset" "$F" | head -25

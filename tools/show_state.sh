#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
F=drivers/gpu/drm/panel/panel-himax-hx83102.c

echo "=== current enable() ==="
awk '/static int hx83102_enable\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$F"

echo
echo "=== probe head ==="
sed -n '1227,1250p' "$F" | cat -n

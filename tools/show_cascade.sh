#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
F=drivers/input/touchscreen/nt36523_fw_update.c

echo "=== cascade_2nd_header_info condition ==="
grep -n "cascade_2nd_header_info" "$F" | head -12

echo
echo "=== how it is computed ==="
awk '/cascade_2nd_header_info *=/{print NR": "$0}' "$F" | head -10

echo
echo "=== fw file header parsing ==="
grep -n -B3 -A25 "bin_map\[" "$F" | head -60

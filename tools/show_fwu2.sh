#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
F=drivers/input/touchscreen/nt36523_fw_update.c

echo "=== Boot_Update_Firmware ==="
awk '/void Boot_Update_Firmware\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$F" | head -50

echo
echo "=== 'done' logging lines ==="
grep -n "Boot_Update_Firmware done" "$F" | head -5

echo
echo "=== globals we could flag ==="
grep -n "^static bool\|^bool\|^static int32_t.*;$\|^int32_t.*;$" "$F" | head -10

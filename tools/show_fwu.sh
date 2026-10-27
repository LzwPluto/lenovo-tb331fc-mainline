#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
TS=drivers/input/touchscreen/nt36523_ts.c

echo "=== Boot_Update_Firmware implementation ==="
awk '/void Boot_Update_Firmware\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$TS" | head -60

echo
echo "=== nvt_update_firmware / return points ==="
grep -n "Boot_Update_Firmware done\|nvt_update_firmware(ts->fw_name)" "$TS" | head -8

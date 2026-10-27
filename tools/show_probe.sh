#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
TS=drivers/input/touchscreen/nt36523_ts.c

echo "=== probe: firmware download section ==="
awk '/static int32_t nvt_ts_probe\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$TS" | grep -nE "Boot_Update_Firmware|nvt_update_firmware|nvt_get_fw_info|input_register|return 0|goto err|NVT_LOG" | head -30

echo
echo "=== Boot_Update_Firmware definition ==="
grep -n "Boot_Update_Firmware" "$TS" | head -10

echo
echo "=== panel probe ==="
awk '/static int hx83102_probe\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' drivers/gpu/drm/panel/panel-himax-hx83102.c | head -40

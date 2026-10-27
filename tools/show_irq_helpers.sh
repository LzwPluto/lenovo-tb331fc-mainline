#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
TS=drivers/input/touchscreen/nt36523_ts.c
FW=drivers/input/touchscreen/nt36523_fw_update.c

echo "=== irq enable/disable helpers ==="
grep -n "nvt_irq_disable\|nvt_irq_enable" "$TS" "$FW" | head -10

echo
echo "=== around nvt_update_firmware (fw_update) ==="
sed -n '800,845p' "$FW"

echo
echo "=== Boot_Update_Firmware current ==="
awk '/^void Boot_Update_Firmware/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$FW" | head -30

#!/bin/bash
set +e
D=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen
echo "=== Boot_Update_Firmware 定义 ==="
grep -n "Boot_Update_Firmware" "$D"/nt36523_fw_update.c "$D"/nt36523_ts.c | head
LN=$(grep -n "void Boot_Update_Firmware" "$D/nt36523_fw_update.c" | head -1 | cut -d: -f1)
echo "at nt36523_fw_update.c:$LN"
sed -n "${LN},$((LN+70))p" "$D/nt36523_fw_update.c"

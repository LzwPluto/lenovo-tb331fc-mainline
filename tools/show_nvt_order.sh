#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c
echo "=== probe 里 restore_cmd_func / update_firmware 的调用顺序 ==="
grep -nE "nvt_restore_cmd_func|nvt_update_firmware|update_firmware_request" "$F" | head -20
echo
echo "=== nvt_restore_cmd_func 函数体 ==="
LN=$(grep -n "^static void nvt_restore_cmd_func\|^void nvt_restore_cmd_func" "$F" | head -1 | cut -d: -f1)
echo "at line $LN"
sed -n "${LN},$((LN+55))p" "$F"
echo
echo "=== probe 里 1700-1780 行 ==="
sed -n '1700,1785p' "$F"

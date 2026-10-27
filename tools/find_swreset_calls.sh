#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen
echo "=== nvt_sw_reset_idle 的所有调用点 ==="
grep -n "nvt_sw_reset_idle\|nvt_sw_reset()\|nvt_bootloader_reset\|nvt_eng_reset" "$K"/nt36523_ts.c "$K"/nt36523_fw_update.c
echo
echo "=== probe 结尾附近（1700-1790）==="
sed -n '1740,1800p' "$K/nt36523_ts.c"

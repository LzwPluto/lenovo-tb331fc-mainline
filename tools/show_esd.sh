#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen
echo "=== ESD 相关宏 ==="
grep -nE "NVT_TOUCH_ESD_PROTECT|NVT_TOUCH_ESD_CHECK_PERIOD|ESD_CHECK" "$K"/nt36523.h "$K"/nt36523_ts.c | head -10
echo
echo "=== 1425-1450 行（sw_reset_idle 调用上下文）==="
sed -n '1415,1455p' "$K/nt36523_ts.c"
echo
echo "=== nvt_esd_check_func 内容 ==="
LN=$(grep -n "static void nvt_esd_check_func" "$K/nt36523_ts.c" | cut -d: -f1)
echo "at $LN"
sed -n "${LN},$((LN+45))p" "$K/nt36523_ts.c"

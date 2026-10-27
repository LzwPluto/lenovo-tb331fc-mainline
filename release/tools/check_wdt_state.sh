#!/bin/bash
# 检查当前触控驱动的关键逻辑状态
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c
echo "=== 是否有激进的单 0xFE 处理（应删除）==="
grep -n "vendor-style reset+reload" "$F"
echo "=== 厂商式 6 字节 + 计数逻辑（应保留）==="
grep -n "all_err\|err_run" "$F" | head -8
echo
echo "=== 当前 WDT 段完整代码 ==="
LN=$(grep -n "all_err" "$F" | head -1 | cut -d: -f1)
[ -n "$LN" ] && sed -n "$((LN-8)),$((LN+42))p" "$F"

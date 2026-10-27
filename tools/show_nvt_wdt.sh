#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c
echo "=== nvt_write_addr 定义/调用 ==="
grep -nE "nvt_write_addr|nvt_write_sram" "$F" | head -10
echo
echo "=== 0xFD/0xFE 分支完整代码 ==="
LN=$(grep -n "Controller WDT reset recovery" "$F" | head -1 | cut -d: -f1)
sed -n "$((LN-3)),$((LN+18))p" "$F"
echo
echo "=== nvt_wdt_fw_recovery ==="
grep -n -A12 "static.*nvt_wdt_fw_recovery" "$F" | head -18

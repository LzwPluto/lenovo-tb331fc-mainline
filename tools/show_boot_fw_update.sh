#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c
echo "=== 2020-2110 行（固件更新 + restore 调用处）==="
sed -n '2020,2110p' "$F"
echo
echo "=== 设备上 4.9s 之后有没有成功的 0xBA ==="

#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1
echo "=== 触控相关 config ==="
grep -E "NT36523|TOUCHSCREEN_NOVATEK|NVT" .config
echo
echo "=== Makefile 里的 nt36523 条目 ==="
grep -n "nt36523" drivers/input/touchscreen/Makefile
echo
echo "=== 心跳是否已加进源码 ==="
grep -n "nvt_hb_work" drivers/input/touchscreen/nt36523_ts.c drivers/input/touchscreen/nt36523.h | head
echo
echo "=== 单独编译该模块 ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M=drivers/input/touchscreen nt36523_ts.ko 2>&1 | tail -25
ls -l drivers/input/touchscreen/nt36523_ts.ko 2>/dev/null || echo "still no .ko"

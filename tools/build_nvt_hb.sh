#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1

echo "=== patch ==="
python3 /mnt/d/TB331FCLinux/tools/add_nvt_heartbeat.py

echo
echo "=== 检查 event_wq 是否在 probe 之前创建 ==="
grep -n "event_wq" drivers/input/touchscreen/nt36523_ts.c | head -8

echo
echo "=== 编译触控模块 ==="
time make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" \
    M=drivers/input/touchscreen modules 2>&1 | tail -20

echo
echo "=== 产物 ==="
ls -l drivers/input/touchscreen/nt36523_ts.ko 2>/dev/null

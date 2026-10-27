#!/bin/bash
# clean build: 只编译并打包，不重复打补丁
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
OUT=${1:-/mnt/d/TB331FCLinux/build/boot_test.img}
cd "$K" || exit 1

python3 /mnt/d/TB331FCLinux/tools/strip_aggressive_fe.py

echo "=== 源码关键逻辑确认 ==="
grep -c "got 0xFE packet -> vendor-style" drivers/input/touchscreen/nt36523_ts.c
grep -c "err_run > 10" drivers/input/touchscreen/nt36523_ts.c
grep -c "pkt rejected, raw" drivers/input/touchscreen/nt36523_ts.c

echo "=== 编译 ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 \
    | grep -iE " error|OBJCOPY" | tail -6

python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode boot \
    --kernel arch/arm64/boot/Image --out "$OUT" 2>&1 | tail -2
ls -l "$OUT"

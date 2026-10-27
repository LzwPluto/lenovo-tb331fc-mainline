#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1
echo "=== build Image (incremental) ==="
time make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 | tail -15
echo
ls -l arch/arm64/boot/Image
echo
echo "=== package boot_b.img ==="
python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode boot \
    --kernel arch/arm64/boot/Image \
    --out /mnt/d/TB331FCLinux/build/boot_hb.img 2>&1 | tail -3
ls -l /mnt/d/TB331FCLinux/build/boot_hb.img

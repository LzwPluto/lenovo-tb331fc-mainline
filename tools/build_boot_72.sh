#!/bin/bash
set +e
K=/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1
echo "=== Building Kernel Image #72 ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 | tail -15
echo "=== Packaging boot_72.img ==="
python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode boot \
    --kernel arch/arm64/boot/Image \
    --out /mnt/d/TB331FCLinux/build/boot_72.img
ls -lh /mnt/d/TB331FCLinux/build/boot_72.img

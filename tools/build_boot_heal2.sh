#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1
python3 /mnt/d/TB331FCLinux/tools/nvt_continuous_selfheal.py
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 \
    | grep -iE " error|OBJCOPY" | tail -6
python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode boot \
    --kernel arch/arm64/boot/Image \
    --out /mnt/d/TB331FCLinux/build/boot_heal2.img 2>&1 | tail -2
ls -l /mnt/d/TB331FCLinux/build/boot_heal2.img

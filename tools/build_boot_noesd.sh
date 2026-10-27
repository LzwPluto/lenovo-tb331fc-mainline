#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1
python3 /mnt/d/TB331FCLinux/tools/nvt_disable_esd_and_poll.py
echo "=== ESD 宏 ==="
grep -n "NVT_TOUCH_ESD_PROTECT" drivers/input/touchscreen/nt36523.h | head -2
echo "=== 编译 ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 | grep -E "error|Error|OBJCOPY" | tail -5
python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode boot \
    --kernel arch/arm64/boot/Image \
    --out /mnt/d/TB331FCLinux/build/boot_noesd.img 2>&1 | tail -2
ls -l /mnt/d/TB331FCLinux/build/boot_noesd.img

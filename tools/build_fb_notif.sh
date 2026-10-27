#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1
python3 /mnt/d/TB331FCLinux/tools/nvt_fb_notifier.py
echo "=== 是否需要 fb.h / fb_notifier 头文件 ==="
grep -nE "#include <linux/fb.h>|fb_register_client" drivers/input/touchscreen/nt36523_ts.c | head -5
echo "=== 编译 ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 | grep -iE "error|OBJCOPY" | tail -8
ls -l arch/arm64/boot/Image

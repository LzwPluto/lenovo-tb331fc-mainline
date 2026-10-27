#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1
python3 /mnt/d/TB331FCLinux/tools/nvt_poll_fallback.py
echo "=== 新心跳函数 ==="
sed -n "$(grep -n 'static void nvt_hb_work_func' drivers/input/touchscreen/nt36523_ts.c | cut -d: -f1),+35p" \
    drivers/input/touchscreen/nt36523_ts.c
echo
echo "=== 编译 ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 | grep -E "error|Error|Image" | tail -6
python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode boot \
    --kernel arch/arm64/boot/Image \
    --out /mnt/d/TB331FCLinux/build/boot_poll.img 2>&1 | tail -2
ls -l /mnt/d/TB331FCLinux/build/boot_poll.img

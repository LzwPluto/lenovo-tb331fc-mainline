#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1

echo "=== 1) 降低触控日志 ===
"
python3 /mnt/d/TB331FCLinux/tools/quiet_console.py

echo "=== 2) 编译 Image ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 \
    | grep -iE " error|OBJCOPY" | tail -5
python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode boot \
    --kernel arch/arm64/boot/Image --out /mnt/d/TB331FCLinux/build/boot_quiet.img 2>&1 | tail -1

echo "=== 3) 重建 vendor_boot：去掉 console=tty0 ==="
cd /mnt/d/TB331FCLinux/build || exit 1
python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode vendor_boot \
    --vendor-ramdisk /mnt/d/TB331FCLinux/initramfs/initramfs_v18.cpio \
    --dtb /mnt/d/TB331FCLinux/build/ref_clamp_final.dtb \
    --cmdline 'console=ttyGS0 keep_bootcon ignore_loglevel clk_ignore_unused pd_ignore_unused rdinit=/init earlycon=qcom_geni,0x4a90000 androidboot.hardware=qcom panic=10' \
    --out /mnt/d/TB331FCLinux/build/vb_quiet.img 2>&1 | tail -2
ls -l /mnt/d/TB331FCLinux/build/boot_quiet.img /mnt/d/TB331FCLinux/build/vb_quiet.img

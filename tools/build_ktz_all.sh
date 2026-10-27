#!/bin/bash
set -e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1

echo "=== config check ==="
grep -n "CONFIG_BACKLIGHT_KTZ8866" .config

echo "=== build kernel ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j10 Image 2>&1 | grep -E " error|Error 1" | head -5 || true
ls -l --time-style=+%H:%M arch/arm64/boot/Image
cp arch/arm64/boot/Image /mnt/d/TB331FCLinux/build/Image_ktz

echo "=== repack vendor_boot with the new DTB ==="
cd /mnt/d/TB331FCLinux || exit 1
python3 tools/repack_vb_dtb2.py build/vb_spidma.img build/CANONICAL_ktz.dtb build/vb_ktz.img 2>&1 | tail -3
python3 tools/verify_vb2.py build/vb_ktz.img 2>&1 | head -12

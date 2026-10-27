#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
cd "$K" || exit 1

echo "=== 1) 撤销 DT 里的 470MHz OPP ==="
python3 /mnt/d/TB331FCLinux/tools/remove_dpu_opp_470.py

echo "=== 2) 给 DPU 驱动加钳位 ==="
python3 /mnt/d/TB331FCLinux/tools/clamp_dpu_clk_to_max_opp.py

echo "=== 3) 编译 ==="
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image 2>&1 \
    | grep -iE " error|OBJCOPY" | tail -6

python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode boot \
    --kernel arch/arm64/boot/Image --out /mnt/d/TB331FCLinux/build/boot_clamp.img 2>&1 | tail -2

echo "=== 4) 重建 DTB（无 470）==="
cd /mnt/d/TB331FCLinux/build || exit 1
dtc -@ -f -I dts -O dtb -o ref_clamp.dtb CANONICAL.dts 2>&1 | grep -E "ERROR|FATAL" | head -3
python3 - <<'PYEOF'
d = bytearray(open('/mnt/d/TB331FCLinux/build/ref_clamp.dtb','rb').read())
old=b'root=/dev/sda18 rw rootwait noinitrd init=/sbin/init console=tty0 PMOS_NOSPLASH'
new=b'console=tty0 rdinit=/init panic=10 clk_ignore_unused pd_ignore_unused'
i=d.find(old)
if i>=0:
    d[i:i+len(old)] = new + b'\0'*(len(old)-len(new))
    open('/mnt/d/TB331FCLinux/build/ref_clamp_final.dtb','wb').write(bytes(d))
    print('bootargs patched')
PYEOF
python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode vendor_boot \
    --vendor-ramdisk /mnt/d/TB331FCLinux/initramfs/initramfs_v18.cpio \
    --dtb /mnt/d/TB331FCLinux/build/ref_clamp_final.dtb \
    --cmdline 'console=tty0 keep_bootcon ignore_loglevel loglevel=8 fbcon=rotate:1 clk_ignore_unused pd_ignore_unused rdinit=/init earlycon=qcom_geni,0x4a90000 androidboot.hardware=qcom panic=10' \
    --out /mnt/d/TB331FCLinux/build/vb_clamp.img 2>&1 | tail -2
ls -l /mnt/d/TB331FCLinux/build/boot_clamp.img /mnt/d/TB331FCLinux/build/vb_clamp.img

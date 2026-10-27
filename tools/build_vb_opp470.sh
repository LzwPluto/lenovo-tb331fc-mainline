#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux/build || exit 1
dtc -@ -f -I dts -O dtb -o ref_opp470.dtb CANONICAL.dts 2>&1 | grep -E "ERROR|FATAL" | head -3
python3 - <<'PYEOF'
d = bytearray(open('/mnt/d/TB331FCLinux/build/ref_opp470.dtb','rb').read())
old=b'root=/dev/sda18 rw rootwait noinitrd init=/sbin/init console=tty0 PMOS_NOSPLASH'
new=b'console=tty0 rdinit=/init panic=10 clk_ignore_unused pd_ignore_unused'
i=d.find(old)
if i<0:
    print('bootargs pattern NOT found')
else:
    d[i:i+len(old)] = new + b'\0'*(len(old)-len(new))
    open('/mnt/d/TB331FCLinux/build/ref_opp470_final.dtb','wb').write(bytes(d))
    print('bootargs patched')
PYEOF
python3 /mnt/d/TB331FCLinux/tools/mkv4.py --mode vendor_boot \
    --vendor-ramdisk /mnt/d/TB331FCLinux/initramfs/initramfs_v18.cpio \
    --dtb /mnt/d/TB331FCLinux/build/ref_opp470_final.dtb \
    --cmdline 'console=tty0 keep_bootcon ignore_loglevel loglevel=8 fbcon=rotate:1 clk_ignore_unused pd_ignore_unused rdinit=/init earlycon=qcom_geni,0x4a90000 androidboot.hardware=qcom panic=10' \
    --out /mnt/d/TB331FCLinux/build/vb_opp470.img 2>&1 | tail -2
ls -l /mnt/d/TB331FCLinux/build/vb_opp470.img

#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== does the kernel tree have any ktz driver? ==="
grep -ril 'ktz8866\|kt,ktz' drivers/ Documentation/ 2>/dev/null | head -5
echo "(empty above = not supported in this tree)"

echo
echo "=== search vendor DTBs for a ktz node ==="
cd /mnt/d/TB331FCLinux || exit 1
for f in build/*.dtb stock_dtbo_entries/*.dtb; do
    [ -f "$f" ] || continue
    hit=$(strings "$f" 2>/dev/null | grep -i 'ktz' | head -2)
    if [ -n "$hit" ]; then
        echo "--- $f"
        echo "$hit"
    fi
done | head -20

echo
echo "=== search vendor DTS sources for ktz / backlight-led nodes ==="
grep -rniE 'ktz|kt,|bkl' build/*.dts 2>/dev/null | head -15

echo
echo "=== i2c buses mentioned in the vendor DT (looking for the LED driver) ==="
grep -nE 'i2c@[0-9a-f]+' build/ov0.dts 2>/dev/null | head -12

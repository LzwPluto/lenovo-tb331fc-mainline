#!/bin/bash
set +e
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts

echo "=== all references to tlmm 0x57 (gpio 87) ==="
grep -n "0x82 0x57 0x00\|0x57 0x00" "$V" | head -10

echo
echo "=== pin definitions mentioning gpio87 ==="
grep -n -B4 -A6 "gpio87" "$V" | head -40

echo
echo "=== any pin state named like bt / sw_ctrl ==="
grep -nE "\*bt[_-]|sw[_-]ctrl|bt_en|bt-en" "$V" | head -12

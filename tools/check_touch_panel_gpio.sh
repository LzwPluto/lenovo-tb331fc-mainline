#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
echo "=== 触摸节点里的复位/中断脚 ==="
grep -n "reset-gpio\|irq-gpio" "$C" | head -8
echo
echo "=== 面板节点（panel@0 / himax）里的 GPIO ==="
grep -n -B3 -A12 "compatible = \"lenovo,p255-inx\"" "$C" | grep -E "gpio|reset|enable|compatible|reg =" | head -20
echo
echo "=== 所有引用 tlmm 0x56 (GPIO 86) 的地方 ==="
grep -n "0x28 0x56" "$C" | head -10
echo
echo "=== gpio 86 / 80 在 Android 上的归属（对照）==="

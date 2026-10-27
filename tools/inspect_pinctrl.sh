#!/bin/bash
set +e
D=/mnt/d/TB331FCLinux/build/CANONICAL.dts
echo "=== tlmm / pinctrl node ==="
grep -n "pinctrl@\|qcom,tlmm\|interrupt-controller;" "$D" | head -8
echo
echo "=== an existing qup pin-state node (qup0 spi) ==="
grep -n -B2 -A8 'pins = "gpio0", "gpio1", "gpio2", "gpio3"' "$D" | head -20
echo
echo "=== spi@4a80000 pinctrl refs ==="
sed -n '/spi@4a80000 {/,/};/p' "$D" | grep -E "pinctrl|phandle" | head -6
echo
echo "=== highest phandle in use ==="
grep -oE "phandle = <0x[0-9a-f]+>" "$D" | grep -oE "0x[0-9a-f]+" | sort -u | tail -3

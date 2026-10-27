#!/bin/bash
set +e
D=/mnt/d/TB331FCLinux/build/CANONICAL.dts
echo "=== phandle 0x47 node (spi pins) ==="
grep -n -B8 "phandle = <0x47>" "$D" | head -20
echo
echo "=== first 4 children of pinctrl@500000 ==="
awk 'NR>=830 && NR<=1000' "$D" | grep -nE "^\t\t\t[a-z0-9_]+ \{|pins =|function =|phandle" | head -24
echo
echo "=== console UART (4a90000) pinctrl ==="
sed -n '/serial@4a90000 {/,/};/p' "$D" | grep -E "pinctrl" | head -4

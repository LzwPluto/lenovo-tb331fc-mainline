#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux/ref/android || exit 1
echo "=== decompile vendor FDT ==="
dtc -f -I dtb -O dts -o vendor.dts vendor.fdt 2>&1 | grep -E "ERROR|FATAL|Warning" | head -5
ls -l vendor.dts 2>/dev/null && wc -l vendor.dts

echo
echo "=== BT serial node in vendor DT ==="
grep -n -A16 'serial@4a8c000' vendor.dts | head -24

echo
echo "=== which serial nodes carry a bluetooth child ==="
grep -n -B20 'wcn3990-bt' vendor.dts | grep -E "serial@|bluetooth|compatible|status" | head -12

#!/bin/bash
# Decompile the vendor dtbo overlays we care about (entries 0 and 2).
set -e
cd /mnt/d/TB331FCLinux/build
for n in 0 2; do
    if [ -f "ov$n.dtb" ]; then
        dtc -f -I dtb -O dts -o "ov$n.dts" "ov$n.dtb" 2>/dev/null || true
        lines=$(wc -l < "ov$n.dts" 2>/dev/null || echo 0)
        echo "ov$n.dts: $lines lines"
    fi
done
echo "--- SD related in ov2 ---"
grep -n -E 'cd-gpios|vmmc-supply|no-sdio|no-mmc|bus-width|sdhc' ov2.dts | head -30 || true
echo "--- SD related in ov0 ---"
grep -n -E 'cd-gpios|vmmc-supply|no-sdio|no-mmc|bus-width|sdhc' ov0.dts | head -30 || true

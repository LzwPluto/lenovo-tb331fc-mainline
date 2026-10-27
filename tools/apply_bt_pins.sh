#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux || exit 1
python3 tools/fix_bt_uart_pins.py
echo "=== serial@4a8c000 now ==="
awk '/serial@4a8c000 \{/,/^\t\t\t\};/' build/CANONICAL.dts | head -16
echo "=== build dtb ==="
cd build || exit 1
dtc -@ -f -I dts -O dtb -o ref_btpins.dtb CANONICAL.dts 2>&1 | grep -E "ERROR|FATAL" | head -3
ls -l ref_btpins.dtb

#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux || exit 1
python3 tools/fix_bt_uart_ctsrts.py
cd build || exit 1
dtc -@ -f -I dts -O dtb -o ref_bt4pin.dtb CANONICAL.dts 2>&1 | grep -E "ERROR|FATAL" | head -3
ls -l ref_bt4pin.dtb

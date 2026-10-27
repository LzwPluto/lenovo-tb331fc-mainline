#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux || exit 1
python3 tools/use_bt_uart_4pin_state.py
awk '/serial@4a8c000 \{/,/pinctrl-0/' build/CANONICAL.dts | tail -3
cd build || exit 1
dtc -@ -f -I dts -O dtb -o ref_bt4p.dtb CANONICAL.dts 2>&1 | grep -E "ERROR|FATAL" | head -3
ls -l ref_bt4p.dtb

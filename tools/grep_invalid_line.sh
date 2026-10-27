#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== who prints 'Invalid line' ==="
grep -rn "Invalid line" drivers/tty/ drivers/ 2>/dev/null | head -5
echo
echo "=== qcom_geni_serial probe line handling ==="
grep -rn -B3 -A12 "Invalid line\|of_alias_get_id" drivers/tty/serial/qcom_geni_serial.c | head -40

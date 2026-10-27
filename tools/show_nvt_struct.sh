#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c
LN=$(grep -n 'struct nvt_ts_data {' "$F" | cut -d: -f1)
echo "struct nvt_ts_data at line $LN"
END=$((LN+70))
sed -n "${LN},${END}p" "$F"
echo
echo "=== probe 里 request_threaded_irq 附近 ==="
IRQ=$(grep -n 'request_threaded_irq' "$F" | cut -d: -f1)
sed -n "$((IRQ-22)),$((IRQ+14))p" "$F"

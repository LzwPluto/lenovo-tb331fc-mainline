#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c
echo "=== 我们驱动里的复位 GPIO 操作 ==="
grep -n "reset_gpio" "$F" | head -20
echo
echo "=== 复位函数上下文 ==="
for LN in $(grep -n "gpio_set_value(ts->reset_gpio" "$F" | cut -d: -f1 | head -3); do
    echo "--- line $LN ---"
    sed -n "$((LN-6)),$((LN+8))p" "$F"
    echo
done

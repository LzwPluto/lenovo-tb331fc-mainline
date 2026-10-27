#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/himax_v3_mmi || exit 1
echo "=== files ==="
ls
echo
echo "=== Makefile ==="
cat Makefile
echo
echo "=== Kconfig (bus selection) ==="
cat Kconfig 2>/dev/null | head -60
echo
echo "=== where does 'Protocol:' come from ==="
grep -rn "Protocol:" --include=*.c .
echo
echo "=== HIMAX_I2C_RETRY_TIMES definition ==="
grep -rn "HIMAX_I2C_RETRY_TIMES" --include=*.h --include=*.c . | head -5
echo
echo "=== SPI vs I2C transfer functions ==="
grep -rn "himax_bus_read\|himax_bus_write\|hx83102_bus_read" --include=*.c . | head -10

#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/himax_v3_mmi || exit 1
echo "=== 'Protocol' log source ==="
grep -rn "Protocol" --include=*.c --include=*.h . | head -10
echo
echo "=== spi transfer functions in platform file ==="
grep -n "spi_sync\|spi_write\|spi_read\|spi_transfer\|himax_bus_read\|himax_bus_write" himax_platform_QCT_SPI.c | head -25
echo
echo "=== sense_off data read ==="
grep -rn "enter_save_mode" --include=*.c . | head -5
echo
echo "=== ic type / ic detect ==="
grep -rn "IC TYPE\|ic_type\|hx83102_ic_type\|IC_TYPE" --include=*.c . | head -10
echo
echo "=== support_ic dir ==="
ls support_ic/
ls support_ic/himax_v3_mmi_hx83102d/ 2>/dev/null

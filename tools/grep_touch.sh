#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== grep: not activated ==="
grep -rn "not activated" --include=*.c --include=*.h . 2>/dev/null | head -10
echo "=== grep: check_dt ==="
grep -rn "check_dt" --include=*.c --include=*.h . 2>/dev/null | head -10
echo "=== grep: panel_active ==="
grep -rn "panel_active" --include=*.c --include=*.h . 2>/dev/null | head -20
echo "=== grep: himax_ts_dt_data / panel ==="
grep -rn "panel" --include=*.c drivers/input/touchscreen/himax_v3_mmi/himax_platform_QCT_SPI.c 2>/dev/null | head -20

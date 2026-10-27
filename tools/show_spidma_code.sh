#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
TS=drivers/input/touchscreen/nt36523_ts.c

echo "=== nvt_spi_dma_setup ==="
awk '/nvt_spi_dma_setup\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$TS" | head -40

echo
echo "=== tx auto copy mode ==="
awk '/nvt_tx_auto_copy_mode\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$TS" | head -30

echo
echo "=== call sites ==="
grep -n "nvt_spi_dma_setup\|nvt_tx_auto_copy_mode" "$TS" | head -10

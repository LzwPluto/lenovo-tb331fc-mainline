#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
F=drivers/input/touchscreen/nt36523_fw_update.c

echo "=== nvt_write_firmware ==="
awk '/int32_t nvt_write_firmware\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$F"

echo
echo "=== write process / chunking helpers ==="
grep -n "CTP_SPI_WRITE\|write_len\|chunk\|0x100\|128\]\|512" "$F" | head -25

echo
echo "=== nvt_check_spi_dma_tx_info ==="
awk '/nvt_check_spi_dma_tx_info\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$F" | head -30

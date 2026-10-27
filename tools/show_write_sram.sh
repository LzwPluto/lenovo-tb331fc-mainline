#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
F=drivers/input/touchscreen/nt36523_fw_update.c

echo "=== NVT_TRANSFER_LEN definition ==="
grep -rn "NVT_TRANSFER_LEN" drivers/input/touchscreen/*.h drivers/input/touchscreen/*.c | head -5

echo
echo "=== nvt_write_sram ==="
awk '/nvt_write_sram\(const u8/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$F" | head -45

echo
echo "=== nvt_check_spi_dma_tx_info body ==="
grep -n -A25 "static int32_t nvt_check_spi_dma_tx_info" "$F" | head -30

#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== nvt_spi_dma_setup (all files) ==="
grep -rn "nvt_spi_dma_setup" drivers/input/touchscreen/ | head
echo
awk '/nvt_spi_dma_setup\(/{f=1} f{print FILENAME" "NR": "$0} f&&/^}/{f=0}' drivers/input/touchscreen/nt36523_fw_update.c | head -45

echo
echo "=== does it poke SPI controller registers? ==="
grep -n "writel\|readl\|iowrite\|GENI_\|0x4a80000\|regmap" drivers/input/touchscreen/nt36523_fw_update.c | head -15

echo
echo "=== SPI_DMA_SETUP_ADDR use ==="
grep -n "SPI_DMA_SETUP_ADDR\|SPI_DMA_TX_INFO" drivers/input/touchscreen/*.c | head -10

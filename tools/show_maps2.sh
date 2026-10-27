#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== who selects the memory map ==="
grep -rn "NT36523N_memory_map\|NT36523_memory_map\|ts->mmap =" drivers/input/touchscreen/*.c | head -20

echo
echo "=== full NT36523N map (boot/BLD/DLM part) ==="
awk '/static const struct nvt_ts_mem_map NT36523N_memory_map/,/^};/' drivers/input/touchscreen/nt36523_mem_map.h | grep -E "BOOT_RDY|POR_CD|TX_AUTO|SPI_DMA|BLD_|ILM_|DLM_|EVENT_BUF|READ_FLASH|RW_FLASH"

echo
echo "=== full NT36523 map (same fields) ==="
awk '/static const struct nvt_ts_mem_map NT36523_memory_map/,/^};/' drivers/input/touchscreen/nt36523_mem_map.h | grep -E "BOOT_RDY|POR_CD|TX_AUTO|SPI_DMA|BLD_|ILM_|DLM_|EVENT_BUF|READ_FLASH|RW_FLASH"

#!/bin/bash
set +e
DIS=/mnt/d/TB331FCLinux/ref/nvt36523_spi.dis

# work_func 范围
awk '/^000000000000369c <nvt_ts_work_func/,/^0000000000004104 <nvt_irq_enable>/' "$DIS" > /tmp/wf.s

echo "=== work_func 中 nvt_write_addr / CTP_SPI_WRITE 调用点上下文 ==="
grep -nE 'bl\s+[0-9a-f]+ <(nvt_write_addr|CTP_SPI_WRITE|CTP_SPI_READ)>' /tmp/wf.s | while IFS=: read -r ln rest; do
    echo "--- line $ln ---"
    start=$((ln-12)); [ $start -lt 1 ] && start=1
    sed -n "${start},$((ln+2))p" /tmp/wf.s
    echo
done

echo "=== nvt_write_addr 函数本体（前 30 行）==="
awk '/^[0-9a-f]+ <nvt_write_addr>:/,/^$/' "$DIS" | head -30

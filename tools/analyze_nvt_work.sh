#!/bin/bash
set +e
DIS=/mnt/d/TB331FCLinux/ref/nvt36523_spi.dis

echo "=== A) IRQ flags 计算（0x27d0 - 0x2830）==="
awk '/^ *27d0:/,/^ *2830:/' "$DIS"

echo
echo "=== B) nvt_ts_work_func 里的函数调用（callee 列表）==="
awk '/^000000000000369c <nvt_ts_work_func/,/^0000000000004104 <nvt_irq_enable>/' "$DIS" \
  | grep -E 'bl\s|b\.\w+\s' | sed 's/.*bl\s//; s/.*b\.\w\+\s//' | sort | uniq -c | sort -rn | head -25

echo
echo "=== C) work_func 里对 gpio 的读取（判断 INT 状态）==="
awk '/^000000000000369c <nvt_ts_work_func/,/^0000000000004104 <nvt_irq_enable>/' "$DIS" \
  | grep -nE 'gpio|get_value|desc' | head -20

#!/bin/bash
# 反汇编厂商 nvt36523_spi.ko，重点找：
#   1) IRQ 触发类型（irq_flags / request_threaded_irq 的参数）
#   2) nvt_ts_work_func 里读包后的循环条件（是否 while (INT 仍为低) 继续读）
#   3) 松手包之后的额外 SPI 写操作（ACK / 清事件队列）
set +e
KO=/mnt/d/TB331FCLinux/ref/nvt36523_spi.ko
OUT=/mnt/d/TB331FCLinux/ref/nvt36523_spi.dis

if [ ! -f "$KO" ]; then echo "missing $KO"; exit 1; fi

aarch64-linux-gnu-objdump -d --no-show-raw-insn "$KO" > "$OUT" 2>/dev/null \
  || objdump -d --no-show-raw-insn "$KO" > "$OUT"
echo "disassembly: $(wc -l < "$OUT") lines -> $OUT"

echo
echo "=== 函数列表（含 nvt_ts_work / irq / reset / ack / clear 的） ==="
grep -E '^[0-9a-f]+ <.*>:' "$OUT" | grep -iE 'work_func|irq|thread|esd|reset|ack|clear|cmd|read_data|report|release' | head -30

echo
echo "=== request_threaded_irq 调用附近（找 flags 参数） ==="
grep -n -B12 'bl.*request_threaded_irq' "$OUT" | grep -E 'mov\s+w[0-9]+, #|bl\s|orr|movz' | tail -30

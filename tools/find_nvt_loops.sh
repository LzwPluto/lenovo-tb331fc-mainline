#!/bin/bash
set +e
DIS=/mnt/d/TB331FCLinux/ref/nvt36523_spi.dis
awk '/^000000000000369c <nvt_ts_work_func/,/^0000000000004104 <nvt_irq_enable>/' "$DIS" > /tmp/wf.s

echo "=== 向后跳转（循环）==="
python3 - <<'PYEOF'
import re
lines = open('/tmp/wf.s').read().split('\n')
cur = 0
loops = []
for ln in lines:
    m = re.match(r'\s*([0-9a-f]+):\s+(\S+)\s+(.*)', ln)
    if not m:
        continue
    addr = int(m.group(1), 16)
    ins, ops = m.group(2), m.group(3)
    if ins.startswith('b') and ins != 'bl':
        t = re.search(r'^\s*([0-9a-f]+)\s', ops)
        if t:
            tgt = int(t.group(1), 16)
            if tgt < addr:
                loops.append((addr, tgt, ins))
for a, t, i in loops:
    print(f'  0x{a:x} {i:12s} -> 0x{t:x}   (循环体 {a-t} 字节)')
PYEOF

echo
echo "=== work_func 前 40 行（看读包前的准备）==="
head -40 /tmp/wf.s

echo
echo "=== 0x3890 之后的正常路径（读包后处理）==="
awk '/^ *3890:/,/^ *3980:/' /tmp/wf.s | head -45

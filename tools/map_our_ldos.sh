#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
start=$(grep -n "regulators-0 {" "$C" | head -1 | cut -d: -f1)
echo "regulators-0 starts at line $start"
python3 - "$C" "$start" <<'PYEOF'
import sys, re
src, start = sys.argv[1], int(sys.argv[2])
lines = open(src, encoding='utf-8').read().split('\n')
i = start - 1
depth = 0
j = i
while j < len(lines):
    depth += lines[j].count('{') - lines[j].count('}')
    if depth == 0 and j > i:
        break
    j += 1
cur = None
for ln in lines[i:j+1]:
    m = re.match(r'\s+([a-z][a-z0-9]*) \{', ln)
    if m:
        cur = m.group(1)
    m2 = re.search(r'phandle = <(0x[0-9a-f]+)>', ln)
    if m2 and cur:
        print(f'  {cur:6s} phandle {m2.group(1)}')
PYEOF

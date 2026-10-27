#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux || exit 1
python3 tools/fix_l17_voltage.py
echo "=== l17 node now ==="
python3 - <<'PYEOF'
import re
t = open('/mnt/d/TB331FCLinux/build/CANONICAL.dts', encoding='utf-8').read()
s = t.find('regulators-0 {')
b = t.index('{', s); d = 0; k = b
while k < len(t):
    d += t[k] == '{'
    d -= t[k] == '}'
    if d == 0 and k > b:
        break
    k += 1
blk = t[b+1:k]
m = re.search(r'l17 \{.*?\n\t+\};', blk, re.S)
print(m.group(0) if m else 'l17 not found')
PYEOF
cd build || exit 1
dtc -@ -f -I dts -O dtb -o ref_l17.dtb CANONICAL.dts 2>&1 | grep -E "ERROR|FATAL" | head -3
ls -l ref_l17.dtb

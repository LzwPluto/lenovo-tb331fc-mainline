#!/bin/bash
set +e
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts
echo "=== vendor qcom,qup_uart@4a8c000 node ==="
sed -n '8862,8900p' "$V"
echo
echo "=== what pinctrl phandle resolves to (search its definition) ==="
python3 - "$V" <<'PYEOF'
import sys, re
src = sys.argv[1]
txt = open(src, encoding='utf-8').read()
lines = txt.split('\n')
start = None
for idx, ln in enumerate(lines):
    if 'qcom,qup_uart@4a8c000' in ln:
        start = idx
        break
if start is None:
    sys.exit('node not found')
depth = 0; j = start
while j < len(lines):
    depth += lines[j].count('{') - lines[j].count('}')
    if depth == 0 and j > start:
        break
    j += 1
node = '\n'.join(lines[start:j+1])
phs = re.findall(r'pinctrl-\d+ = <(0x[0-9a-f]+)(?: (0x[0-9a-f]+))?(?: (0x[0-9a-f]+))?>;', node)
print('pinctrl refs:', phs)
for tup in phs:
    for ph in tup:
        if not ph:
            continue
        for k, ln in enumerate(lines):
            if f'phandle = <{ph}>' in ln:
                # walk backwards to find the node name
                for b in range(k, max(0, k-12), -1):
                    m = re.match(r'\s+([a-z0-9_,@-]+) \{', lines[b])
                    if m:
                        print(f'  {ph} -> {m.group(1)}')
                        break
                break
PYEOF

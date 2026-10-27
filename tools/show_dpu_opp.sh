#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
echo "=== DPU 的 operating-points-v2 指向 ==="
python3 - <<'PYEOF'
import re
t = open('/mnt/d/TB331FCLinux/build/CANONICAL.dts', encoding='utf-8').read()
i = t.find('display-controller@5e01000 {')
if i < 0:
    print('dpu node not found'); raise SystemExit
b = t.index('{', i); d = 0; k = b
while k < len(t):
    d += t[k] == '{'; d -= t[k] == '}'
    if d == 0 and k > b: break
    k += 1
node = t[b+1:k]
m = re.search(r'operating-points-v2 = <(0x[0-9a-f]+)>;', node)
print('  operating-points-v2 phandle =', m.group(1) if m else 'none')
ph = m.group(1) if m else None
if ph:
    # locate the opp table node defining that phandle
    for mm in re.finditer(r'(\n\t+)([a-z0-9_,@.-]+) \{', t):
        bb = t.index('{', mm.start()); dd = 0; kk = bb
        while kk < len(t):
            dd += t[kk] == '{'; dd -= t[kk] == '}'
            if dd == 0 and kk > bb: break
            kk += 1
        body = t[bb:kk+1]
        if f'phandle = <{ph}>' in body and 'opp-hz' in body:
            print(f'  -> opp table node: {mm.group(2)}')
            for line in body.split('\n'):
                s = line.strip()
                if s.startswith(('opp-', 'opp-hz', 'opp-microvolt', 'phandle', 'opp-supported')):
                    print('     ' + s)
            break
PYEOF

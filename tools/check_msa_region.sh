#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
V=/mnt/d/TB331FCLinux/ref/android/vendor.dts

echo "=== OUR dts: wifi memory-region phandle and its node ==="
python3 - <<'PYEOF'
import re
t = open('/mnt/d/TB331FCLinux/build/CANONICAL.dts', encoding='utf-8').read()

i = t.find('wifi@c800000 {')
if i < 0:
    print('wifi node not found'); raise SystemExit
j = t.index('{', i); d = 0; k = j
while k < len(t):
    d += t[k] == '{'; d -= t[k] == '}'
    if d == 0 and k > j: break
    k += 1
node = t[i:k+1]
m = re.search(r'memory-region = <(0x[0-9a-f]+)>;', node)
print('  memory-region phandle =', m.group(1) if m else 'NOT FOUND')
ph = m.group(1) if m else None

if ph:
    # find the node that defines this phandle
    for mm in re.finditer(r'(\n\t+)([a-z0-9_,@.-]+) \{', t):
        start = mm.start()
        depth = 0; e = t.index('{', start); p = e
        while p < len(t):
            depth += t[p] == '{'; depth -= t[p] == '}'
            if depth == 0 and p > e: break
            p += 1
        body = t[e:p+1]
        if f'phandle = <{ph}>' in body:
            print(f'  -> node: {mm.group(2)}')
            for line in body.split('\n'):
                if any(x in line for x in ('reg =', 'no-map', 'reusable', 'compatible', 'size')):
                    print('     ' + line.strip())
            break
PYEOF

echo
echo "=== VENDOR dts: wlan_msa_region ==="
grep -n -A6 'wlan_msa_region' "$V" | head -12

echo
echo "=== OUR dts: all reserved-memory regs (first 12) ==="
grep -n -A3 'reserved-memory {' "$C" | head -6
grep -nE '^\t\t[a-z0-9_,@.-]+ \{$' "$C" | head -0

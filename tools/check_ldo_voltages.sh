#!/bin/bash
set +e
C=/mnt/d/TB331FCLinux/build/CANONICAL.dts
start=$(grep -n "regulators-0 {" "$C" | head -1 | cut -d: -f1)
python3 - "$C" "$start" <<'PYEOF'
import sys, re
src, start = sys.argv[1], int(sys.argv[2])
lines = open(src, encoding='utf-8').read().split('\n')
i = start - 1
depth = 0; j = i
while j < len(lines):
    depth += lines[j].count('{') - lines[j].count('}')
    if depth == 0 and j > i:
        break
    j += 1
block = lines[i:j+1]
cur = None
vals = {}
for ln in block:
    m = re.match(r'\s+([a-z][a-z0-9]*) \{', ln)
    if m:
        cur = m.group(1); vals.setdefault(cur, {})
    if cur:
        for prop in ('regulator-min-microvolt', 'regulator-max-microvolt',
                     'regulator-boot-on', 'regulator-always-on'):
            m2 = re.search(prop.replace('-', r'\-') + r' = <(0x[0-9a-f]+)>;', ln)
            if m2:
                vals[cur][prop] = int(m2.group(1), 16)
            elif prop in ln and 'boot-on' in prop:
                vals[cur][prop] = True
            elif prop in ln and 'always-on' in prop:
                vals[cur][prop] = True

want = {'l9': (1700000, 1900000), 'l16': (1700000, 1900000),
        'l17': (1304000, 1304000), 'l23': (3000000, 3300000)}
for k in ('l8', 'l9', 'l16', 'l17', 'l22', 'l23', 'l24'):
    v = vals.get(k, {})
    exp = want.get(k)
    line = f'  {k:4s} min={v.get("regulator-min-microvolt", "-"):>8} max={v.get("regulator-max-microvolt", "-"):>8}'
    if exp:
        line += f'   vendor expects {exp[0]}..{exp[1]}'
        lo = v.get('regulator-min-microvolt'); hi = v.get('regulator-max-microvolt')
        if lo is not None and hi is not None:
            line += '  ' + ('OK' if (lo <= exp[1] and hi >= exp[0]) else '*** MISMATCH ***')
    print(line)
PYEOF

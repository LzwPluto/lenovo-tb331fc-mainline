#!/usr/bin/env python3
"""add_dpu_opp_470.py

dpu_core_perf_crtc_update() asks dev_pm_opp_set_rate() for 470 MHz, but the DPU's
OPP table only contains 384 MHz, so the call fails:

    dev_pm_opp_set_rate: failed to find OPP for freq 470000000 (-34)
    [dpu error] failed to set core clock rate 384000000

The display then runs with an unstable core clock, which shows up as stripes in
Niri.  dispcc only supports 19.2/192/256/307.2/384 MHz, but clk_set_rate() rounds
down to the closest supported rate instead of failing - so adding a 470 MHz OPP
entry both satisfies the OPP lookup and leaves the clock at 384 MHz.

Add the entry, keeping the existing 384 MHz one.
"""
import re
import sys

P = '/mnt/d/TB331FCLinux/build/CANONICAL.dts'
t = open(P, encoding='utf-8').read()

if 'opp-470000000' in t:
    print('470 MHz OPP already present')
    sys.exit(0)

# find the opp-table node that owns phandle 0x72 (the DPU's operating-points-v2)
target = None
for m in re.finditer(r'opp-table \{', t):
    brace = t.index('{', m.start())
    depth = 0; k = brace
    while k < len(t):
        if t[k] == '{':
            depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    body = t[brace:k + 1]
    if 'phandle = <0x72>;' in body:
        target = (brace, k, body)
        break

if not target:
    sys.exit('DPU opp-table (phandle 0x72) not found')

brace, end, body = target

# insert a 470 MHz entry right after the opening brace, matching the file's tabs
mm = re.search(r'\n(\t+)opp-384000000 \{', body)
if not mm:
    sys.exit('existing opp-384000000 entry not found - unexpected table layout')
indent = mm.group(1)

entry = (f'\n{indent}opp-470000000 {{'
         f'\n{indent}\topp-hz = <0x00 0x1c04c600>;'   # 470000000
         f'\n{indent}}};')

t = t[:brace + 1] + entry + t[brace + 1:]
open(P, 'w', encoding='utf-8', newline='\n').write(t)
print('added opp-470000000 (0x1c04c600) to the DPU OPP table')

# show the result
t2 = open(P, encoding='utf-8').read()
i = t2.find('opp-470000000')
print(t2[i - 60:i + 120])

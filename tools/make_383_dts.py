#!/usr/bin/env python3
"""make_383_dts.py

Rewrite the DPU operating-points table (phandle 0x72) so it contains a single
383000000 entry, then the DPU core clock can never be moved off the one rate
dispcc-sm6225.c can actually produce from the current parent:
    F(383000000, P_DISP_CC_PLL0_OUT_MAIN, 2, 0, 0)

Why the other entries are poison:
    F(200000000, P_GCC_DISP_GPLL0_DIV_CLK_SRC, 1.5, 0, 0)
    F(300000000, P_GCC_DISP_GPLL0_DIV_CLK_SRC, 1,   0, 0)
  both need the RCG to switch parent to GCC_DISP_GPLL0_DIV_CLK_SRC and retune it;
  dpu_core_perf asks for 200 MHz, clk_set_rate() fails with -EINVAL, and the
  failed transition leaves disp_cc_mdss_mdp_clk at the 19.2 MHz minimum -> the
  display is starved -> stripes / blue-green grid.
    F(470000000 / F(560000000, P_DISP_CC_PLL0_OUT_MAIN, 2, ...)  are simply wrong
  (same divider as 383 MHz).

With a single OPP, dev_pm_opp_find_freq_ceil()/floor() can only return 383 MHz
and dev_pm_opp_set_rate() always succeeds.
"""
import re
import sys

SRC = '/mnt/d/TB331FCLinux/build/CANONICAL_oppfix.dts'
DST = '/mnt/d/TB331FCLinux/build/CANONICAL_383.dts'

t = open(SRC, encoding='utf-8').read()

start = t.find('phandle = <0x72>;')
if start < 0:
    sys.exit('DPU opp-table (phandle 0x72) not found')

# the opp-table's own closing brace is the first 4-tab "};" after the entries
m = re.search(r'\n\t{4}\};', t[start:])
if not m:
    sys.exit('opp-table closing brace not found')
end = start + m.start()

OLD_ENTRIES = t[start:end]

NEW = ('phandle = <0x72>;\n'
       '\n'
       '\t\t\t\t\topp-383000000 {\n'
       '\t\t\t\t\t\topp-hz = <0x00 0x16d41dc0>;\n'
       '\t\t\t\t\t\trequired-opps = <0x3a>;\n'
       '\t\t\t\t\t};')

print('replacing:')
for mm in re.finditer(r'opp-(0x[0-9a-f]+|\d+)', OLD_ENTRIES):
    pass
for mm in re.finditer(r'opp-hz = <0x00 (0x[0-9a-f]+)>', OLD_ENTRIES):
    print(f'  {int(mm.group(1), 16):>12} Hz')
print('with:')
print('      383000000 Hz')

t = t[:start] + NEW + t[end:]
open(DST, 'w', encoding='utf-8', newline='\n').write(t)
print(f'wrote {DST}')

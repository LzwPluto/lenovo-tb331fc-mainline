#!/usr/bin/env python3
"""fix_dpu_opp_table.py

Restore the vendor's 6-entry DPU OPP table (19.2/200/300/383/470/560 MHz).

Why: the current CANONICAL.dts has a single opp-384000000 entry.  The dispcc
MDP clock only supports 383 MHz (not 384), and high-bandwidth use (Niri) needs
470 MHz.  The result was:

    dev_pm_opp_set_rate: failed to find OPP for freq 470000000 (-34)
    [dpu error] failed to set core clock rate 384000000

i.e. the DPU core clock never got set, the pipe underran, and the panel showed
stripes.  All six rates below match ftbl_disp_cc_mdss_mdp_clk_src exactly.
"""
import re
import sys

SRC = r'D:\TB331FCLinux\build\CANONICAL.dts'
DST = r'D:\TB331FCLinux\build\CANONICAL_oppfix.dts'

t = open(SRC, encoding='utf-8').read()

# locate the DPU opp-table: the one whose phandle is 0x72
m = re.search(r'[ \t]*opp-table \{[^}]*?phandle = <0x72>;', t, re.S)
if not m:
    sys.exit('DPU opp-table (phandle 0x72) not found')

start = m.start()
# walk braces from the opening { of that node
j = t.index('{', start)
depth = 0
k = j
while k < len(t):
    if t[k] == '{':
        depth += 1
    elif t[k] == '}':
        depth -= 1
        if depth == 0:
            break
    k += 1
# the original block ends with "};};" - swallow the trailing close of the parent
end = k + 1
rest = t[end:]
mm = re.match(r'\s*\}', rest)
if mm:
    end += mm.end()

new = '''opp-table {
					compatible = "operating-points-v2";
					phandle = <0x72>;

					opp-19200000 {
						opp-hz = <0x00 0x124f800>;
						required-opps = <0x75>;
					};

					opp-200000000 {
						opp-hz = <0x00 0xbebc200>;
						required-opps = <0x18>;
					};

					opp-300000000 {
						opp-hz = <0x00 0x11e1a300>;
						required-opps = <0x19>;
					};

					opp-383000000 {
						opp-hz = <0x00 0x16d41dc0>;
						required-opps = <0x3a>;
					};

					opp-470000000 {
						opp-hz = <0x00 0x1c03a180>;
						required-opps = <0x1a>;
					};

					opp-560000000 {
						opp-hz = <0x00 0x2160ec00>;
						required-opps = <0x6e>;
					};
				};'''

t2 = t[:start] + new + t[end:]
open(DST, 'w', encoding='utf-8', newline='\n').write(t2)

print(f'replaced DPU opp-table: {end-start} bytes -> {len(new)} bytes')
print(f'wrote {DST}')
for line in new.split('\n'):
    if 'opp-hz' in line or 'opp-' in line:
        print('   ', line.strip())

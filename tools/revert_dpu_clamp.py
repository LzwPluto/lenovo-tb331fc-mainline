#!/usr/bin/env python3
"""revert_dpu_clamp.py - remove the TB331FC OPP clamp block from
dpu_core_perf.c, restoring the upstream code path.

The clamp was written when the DT had a single opp-384000000 entry.  The DT now
carries the vendor's six operating points (192/200/300/383/470/560 MHz), so the
clamp is a no-op at best and a source of confusion at worst.
"""
import os
import sys

P = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c')
s = open(P, encoding='utf-8').read()

start = s.find('\t\t/*\n\t\t * TB331FC: clamp to the highest OPP')
if start < 0:
    print('clamp block not found (already reverted?)')
    sys.exit(0)

end = s.find('clk_rate = min(clk_rate, kms->perf.max_core_clk_rate);', start)
if end < 0:
    sys.exit('end anchor not found')

block = s[start:end]
print(f'removing {len(block)} bytes of clamp code')
s = s[:start] + s[end:]

open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('dpu_core_perf.c: clamp removed, upstream path restored')

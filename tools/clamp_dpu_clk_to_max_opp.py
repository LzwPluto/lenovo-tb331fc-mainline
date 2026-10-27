#!/usr/bin/env python3
"""clamp_dpu_clk_to_max_opp.py

The DPU asks for a 470 MHz core clock.  dispcc can be programmed to 470 MHz but
the display pipeline produces stripes at that rate; 384 MHz is the correct
operating point (and is the only OPP described in the DT).

dpu_core_perf_crtc_update() already tries to clamp with

    clk_rate = min(clk_rate, kms->perf.max_core_clk_rate);

but max_core_clk_rate resolves to 470 MHz here, so the clamp does nothing and
dev_pm_opp_set_rate() either fails (OPP absent) or programs 470 MHz (stripes).

Clamp to the highest OPP actually present in the table instead.
"""
import sys

F = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c'
s = open(F, encoding='utf-8').read()

if 'max_opp_rate' in s:
    print('already patched')
    sys.exit(0)

old = '''		clk_rate = min(clk_rate, kms->perf.max_core_clk_rate);
		/*'''
new = '''		/*
		 * TB331FC: clamp to the highest OPP present in the DT.  The
		 * display pipeline shows stripes at 470 MHz, and 384 MHz is the
		 * operating point described by the OPP table.
		 */
		{
			unsigned long max_opp_rate = ULONG_MAX;
			struct dev_pm_opp *max_opp;

			max_opp = dev_pm_opp_find_freq_floor(&kms->pdev->dev,
							     &max_opp_rate);
			if (!IS_ERR(max_opp)) {
				clk_rate = min_t(u64, clk_rate,
						 dev_pm_opp_get_freq(max_opp));
				dev_pm_opp_put(max_opp);
			}
		}

		clk_rate = min(clk_rate, kms->perf.max_core_clk_rate);
		/*'''

if old not in s:
    sys.exit('anchor not found in dpu_core_perf.c')

s = s.replace(old, new, 1)

# make sure ULONG_MAX / min_t are available
if '#include <linux/limits.h>' not in s:
    s = s.replace('#include <linux/kernel.h>',
                  '#include <linux/kernel.h>\n#include <linux/limits.h>', 1)

open(F, 'w', encoding='utf-8', newline='\n').write(s)
print('dpu_core_perf.c: core clock clamped to the highest OPP')

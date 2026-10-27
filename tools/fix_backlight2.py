#!/usr/bin/env python3
"""fix_backlight2.py

Empirical finding: this panel's DCS 0x51 takes the brightness as a plain 12-bit
value in normal byte order.

  * (((v & 0xFF) << 8) | (v >> 8)) on a 12-bit value is always huge
    (e.g. 100 -> 0x6400 = 25600) and clamps to maximum -> "brightness never
    changes", which is exactly what the hardware showed.
  * the original "4095 - v" also ends up near maximum for most of the range.

So: send the raw value (clamped), and log a rate-limited error when the DSI
transfer fails so we can tell "command rejected" from "command ignored".
"""
import os
import sys

P = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c')

s = open(P, encoding='utf-8').read()

OLD = """	if (brightness > 4095)
		brightness = 4095;

	/*
	 * qcom,mdss-dsi-bl-inverted-dbv means the DBV *byte order* is inverted,
	 * exactly like Qualcomm's dsi_panel.c:
	 *     bl_lvl = ((bl_lvl & 0xFF) << 8) | (bl_lvl >> 8);
	 * Doing "4095 - v" instead makes the panel read a byte-swapped (huge)
	 * value and clamp to maximum, which looks like "brightness never changes".
	 */
	if (ctx->desc->inverted_dbv)
		brightness = ((brightness & 0xFF) << 8) | (brightness >> 8);

	return mipi_dsi_dcs_set_display_brightness_large(ctx->dsi, brightness);
}"""

NEW = """	int ret;

	if (brightness > 4095)
		brightness = 4095;

	/*
	 * This panel (Novatek NT36523N / p255_inx) takes a plain 12-bit value in
	 * normal byte order.  Both alternatives were measured on hardware:
	 *   - "4095 - v"        -> value stays near maximum for most of the range
	 *   - swab16 of a 12-bit value -> always >= 0x1000, clamps to maximum
	 * Either one makes the slider appear to do nothing.  Send it as-is.
	 */
	ret = mipi_dsi_dcs_set_display_brightness_large(ctx->dsi, brightness);
	if (ret < 0)
		dev_err_ratelimited(&ctx->dsi->dev,
				    "backlight 0x51 write failed (%d), val=%u\\n",
				    ret, brightness);

	return ret;
}"""

if NEW in s:
    print('already patched')
    sys.exit(0)
if OLD not in s:
    sys.exit('bl_write body not recognised')
s = s.replace(OLD, NEW, 1)
open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('backlight: raw 12-bit value + rate-limited error log')

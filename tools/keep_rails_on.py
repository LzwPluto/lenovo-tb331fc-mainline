#!/usr/bin/env python3
"""keep_rails_on.py

Root cause of the touch/display conflict:
  hx83102_unprepare() cuts the panel rails (1V8 pp1800 + avdd + avee).  The
  Novatek TDDI shares that 1V8 rail, so it loses its firmware on every modeset.
  Re-downloading the firmware (the old hook) is a bulk SPI write to the same
  die and disturbs the display engine -> content-dependent stripes.  Moving the
  reload earlier (before the DSI init) does not help either: the DSI init that
  follows knocks the touch side out again.

Fix: keep the rails powered.  The panel is still reset and re-initialised on
every prepare(), so the display is unaffected, but the touch controller never
loses power or firmware -- so no reload is needed at all and the hook can go.
"""
import os
import sys

PN = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c')

s = open(PN, encoding='utf-8').read()

if 'TB331FC rails stay on' in s:
    print('already patched')
    sys.exit(0)

# ---- 1. unprepare(): stop cutting the rails ----
OLD_UNPREP = """	gpiod_set_value(ctx->enable_gpio, 0);
	usleep_range(1000, 2000);
	if (ctx->avee)
		regulator_disable(ctx->avee);
	if (ctx->avdd)
		regulator_disable(ctx->avdd);
	usleep_range(5000, 7000);
	regulator_disable(ctx->pp1800);

	return 0;
}"""
NEW_UNPREP = """	gpiod_set_value(ctx->enable_gpio, 0);
	usleep_range(1000, 2000);

	/*
	 * TB331FC rails stay on: the Novatek TDDI shares the panel's 1V8 rail and
	 * loses its firmware whenever it is power cycled, and reloading that
	 * firmware over SPI disturbs the display engine (content-dependent
	 * stripes).  Keeping the rails up across modesets keeps the touch
	 * controller alive, which removes the need for any reload.
	 * The panel itself is still reset + re-initialised in prepare().
	 */
	ctx->rails_kept_on = true;

	return 0;
}"""

if OLD_UNPREP not in s:
    sys.exit('unprepare() body not recognised')
s = s.replace(OLD_UNPREP, NEW_UNPREP, 1)

# ---- 2. prepare(): only power up when the rails are actually off ----
OLD_PWR = """	dsi_ctx.accum_err = regulator_enable(ctx->pp1800);
	if (dsi_ctx.accum_err)
		return dsi_ctx.accum_err;

	usleep_range(3000, 5000);

	if (ctx->avdd) {
		dsi_ctx.accum_err = regulator_enable(ctx->avdd);
		if (dsi_ctx.accum_err)
			goto poweroff1v8;
	}
	if (ctx->avee) {
		dsi_ctx.accum_err = regulator_enable(ctx->avee);
		if (dsi_ctx.accum_err)
			goto poweroffavdd;
	}
"""
NEW_PWR = """	if (!ctx->rails_kept_on) {
		dsi_ctx.accum_err = regulator_enable(ctx->pp1800);
		if (dsi_ctx.accum_err)
			return dsi_ctx.accum_err;

		usleep_range(3000, 5000);

		if (ctx->avdd) {
			dsi_ctx.accum_err = regulator_enable(ctx->avdd);
			if (dsi_ctx.accum_err)
				goto poweroff1v8;
		}
		if (ctx->avee) {
			dsi_ctx.accum_err = regulator_enable(ctx->avee);
			if (dsi_ctx.accum_err)
				goto poweroffavdd;
		}
	}
"""
if OLD_PWR not in s:
    sys.exit('prepare() power-up block not recognised')
s = s.replace(OLD_PWR, NEW_PWR, 1)

# ---- 3. drop the touch hook call from prepare() ----
HOOK = """	if (nvt_ts_panel_event)
		nvt_ts_panel_event(true);

"""
if HOOK in s:
    s = s.replace(HOOK, '', 1)
    print('removed touch hook call from prepare()')

# ---- 4. add the flag to the ctx struct ----
OLD_STRUCT = '	struct gpio_desc *enable_gpio;'
NEW_STRUCT = '	struct gpio_desc *enable_gpio;\n\tbool rails_kept_on;'
if OLD_STRUCT not in s:
    sys.exit('ctx struct anchor not found')
s = s.replace(OLD_STRUCT, NEW_STRUCT, 1)

open(PN, 'w', encoding='utf-8', newline='\n').write(s)
print('patched: rails stay powered, touch hook removed from panel driver')

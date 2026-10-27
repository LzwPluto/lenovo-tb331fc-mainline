#!/usr/bin/env python3
"""touch_then_reinit_panel.py

Observed behaviour (from the user):
  * stripes appear at ~13-14 s, which is exactly when the touch firmware is
    downloaded over SPI, and they persist ...
  * ... until niri starts, i.e. until the panel goes through a full modeset
    (disable + prepare + enable) which re-sends the panel init sequence.

So a bulk SPI write to this TDDI corrupts the *display* state, and re-running
the panel init sequence repairs it.

Therefore: keep the touch firmware reload (it is what makes touch work) but make
it synchronous, and immediately re-send the panel init sequence afterwards.
That gives working touch and a clean display without an extra modeset.
"""
import os
import shutil
import sys

PN = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c')
TS = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c')

s = open(PN, encoding='utf-8').read()

if 're-run the panel init' in s:
    print('already patched')
    sys.exit(0)

# ---- 1. prepare(): drop the "keep rails on" hack? keep it (harmless) ----
# ---- 2. enable(): touch reload (synchronous) then re-init the panel ----
OLD_ENABLE = """	msleep(130);

	if (ctx->backlight)
		backlight_update_status(ctx->backlight);

	/* touch re-init happens in prepare(), before DSI init */

	return 0;
}"""

NEW_ENABLE = """	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	msleep(130);

	if (ctx->backlight)
		backlight_update_status(ctx->backlight);

	/*
	 * The Novatek TDDI needs its firmware reloaded after the panel is
	 * (re)initialised, but that bulk SPI write corrupts the TDDI display
	 * state (content-dependent stripes, seen from ~14 s until the first
	 * modeset).  Re-running the panel init sequence afterwards repairs the
	 * display, which is why a modeset was the only thing that cleared the
	 * stripes before.
	 */
	if (nvt_ts_panel_event) {
		nvt_ts_panel_event(true);        /* synchronous firmware reload */

		ctx->desc->init(ctx);
		mipi_dsi_dcs_exit_sleep_mode_multi(&dsi_ctx);
		mipi_dsi_msleep(&dsi_ctx, 120);
		mipi_dsi_dcs_set_display_on_multi(&dsi_ctx);
		if (dsi_ctx.accum_err)
			return dsi_ctx.accum_err;
	}

	return 0;
}"""

if OLD_ENABLE not in s:
    sys.exit('hx83102_enable() body not recognised')
s = s.replace(OLD_ENABLE, NEW_ENABLE, 1)
open(PN, 'w', encoding='utf-8', newline='\n').write(s)
print('enable(): synchronous touch reload + panel re-init')

# ---- 3. make sure the touch hook is synchronous ----
t = open(TS, encoding='utf-8').read()
if 'nvt_panel_on_work(NULL)' not in t:
    OLD_EVENT = """void nvt_ts_panel_event(bool on)
{
	if (!ts)
		return;

	if (on)
		schedule_work(&nvt_panel_work);
}"""
    NEW_EVENT = """/* synchronous: the caller re-initialises the panel right after we return */
void nvt_ts_panel_event(bool on)
{
	if (!ts || !on)
		return;

	cancel_work_sync(&nvt_panel_work);
	nvt_panel_on_work(NULL);
}"""
    if OLD_EVENT not in t:
        sys.exit('nvt_ts_panel_event body not recognised')
    t = t.replace(OLD_EVENT, NEW_EVENT, 1)
    open(TS, 'w', encoding='utf-8', newline='\n').write(t)
    print('touch hook made synchronous')
else:
    print('touch hook already synchronous')

#!/usr/bin/env python3
"""order_touch_before_display.py

The real fix for "firmware download vs display must not interfere".

Facts established on the device:
  * touch probe at ~9 s, then a delayed work (2500 ms) downloads the touch
    firmware over SPI at ~11.5-13 s;
  * the panel is already up and scanning at ~5 s, so that bulk SPI write
    corrupts the TDDI display state -> content-dependent stripes until the next
    full modeset;
  * any *re-download* while the panel is scanning recreates the stripes.

So the only clean ordering is: touch firmware first, display afterwards.
Implement it by making the panel probe wait for a "touch fw ready" flag that the
touch driver sets when Boot_Update_Firmware() finishes.  After that the panel is
registered, enabled and never disturbs the touch again (the rails are kept up so
the controller keeps its firmware).
"""
import os
import sys

BASE = os.path.expanduser('~/kbuild/linux-next-tb128fu-hx83102-panel-port')
PN = os.path.join(BASE, 'drivers/gpu/drm/panel/panel-himax-hx83102.c')
FW = os.path.join(BASE, 'drivers/input/touchscreen/nt36523_fw_update.c')

p = open(PN, encoding='utf-8').read()

if 'touch fw ready=' in p:
    print('panel already patched')
else:
    # --- 1. weak extern declaration ---
    OLD_DECL = 'extern void nvt_ts_panel_event(bool on) __attribute__((weak));'
    NEW_DECL = (OLD_DECL + '\n'
                '/* set by the touch driver once its firmware download finished */\n'
                'extern bool nvt_fw_ready __attribute__((weak));')
    if OLD_DECL not in p:
        sys.exit('hook extern declaration not found')
    p = p.replace(OLD_DECL, NEW_DECL, 1)

    # --- 2. enable(): drop the reload+reinit completely ---
    OLD_ENABLE = """	msleep(130);

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
    NEW_ENABLE = """	msleep(130);

	if (ctx->backlight)
		backlight_update_status(ctx->backlight);

	/*
	 * No touch re-init here.  The Novatek TDDI firmware download is a bulk
	 * SPI write to the same die and corrupts the display while the panel is
	 * scanning, so it is ordered *before* the panel is brought up instead
	 * (see the wait in hx83102_probe()).
	 */

	return 0;
}"""
    if OLD_ENABLE not in p:
        sys.exit('enable() body not recognised')
    p = p.replace(OLD_ENABLE, NEW_ENABLE, 1)

    # the dsi_ctx local is now unused in enable()
    p = p.replace("""	struct hx83102 *ctx = panel_to_hx83102(panel);

	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	msleep(130);""",
                  """	struct hx83102 *ctx = panel_to_hx83102(panel);

	msleep(130);""", 1)

    # --- 3. probe(): wait for the touch firmware before registering ---
    OLD_PROBE = """	ctx->desc = desc;
	ctx->dsi = dsi;
	ret = hx83102_panel_add(ctx);"""
    NEW_PROBE = """	ctx->desc = desc;
	ctx->dsi = dsi;

	/*
	 * TB331FC: the Novatek TDDI downloads its firmware over SPI shortly after
	 * it probes.  That bulk write corrupts the display engine if the panel is
	 * already scanning, so wait here until it has finished before registering
	 * (and thereby enabling) the panel.  nvt_fw_ready is a weak symbol: if the
	 * touch driver is not built in, the display must still come up.
	 */
	if (&nvt_fw_ready != NULL) {
		int i;

		for (i = 0; i < 400 && !nvt_fw_ready; i++)
			msleep(50);
		dev_info(&dsi->dev, "touch fw ready=%d after %d ms\\n",
			 nvt_fw_ready, i * 50);
	}

	ret = hx83102_panel_add(ctx);"""
    if OLD_PROBE not in p:
        sys.exit('probe() anchor not found')
    p = p.replace(OLD_PROBE, NEW_PROBE, 1)

    open(PN, 'w', encoding='utf-8', newline='\n').write(p)
    print('panel: waits for touch fw, no reload in enable()')

# --- 4. touch driver: publish the ready flag ---
f = open(FW, encoding='utf-8').read()
if 'nvt_fw_ready = true' not in f:
    OLD_FWU = 'void Boot_Update_Firmware(struct work_struct *work)\n{'
    NEW_FWU = ('/* read by the panel driver to order the display after the touch fw load */\n'
               'bool nvt_fw_ready;\n'
               'EXPORT_SYMBOL_GPL(nvt_fw_ready);\n'
               '\n'
               'void Boot_Update_Firmware(struct work_struct *work)\n{')
    if OLD_FWU not in f:
        sys.exit('Boot_Update_Firmware anchor not found')
    f = f.replace(OLD_FWU, NEW_FWU, 1)

    OLD_TAIL = '\tnvt_ts_work_func(ts->client->irq, ts);'
    NEW_TAIL = ('\tnvt_ts_work_func(ts->client->irq, ts);\n'
                '\n'
                '\t/* firmware is loaded and scanning: let the panel come up now */\n'
                '\tnvt_fw_ready = true;')
    if OLD_TAIL not in f:
        sys.exit('Boot_Update_Firmware tail not found')
    f = f.replace(OLD_TAIL, NEW_TAIL, 1)
    open(FW, 'w', encoding='utf-8', newline='\n').write(f)
    print('touch: nvt_fw_ready published')
else:
    print('touch already patched')

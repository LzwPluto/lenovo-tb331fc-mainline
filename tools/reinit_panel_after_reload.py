#!/usr/bin/env python3
"""reinit_panel_after_touch_reload.py

Now that the touch firmware download actually succeeds (4 KiB chunks), the only
remaining problem is that the download disturbs the panel's display state: the
stripes start around the first NVT activity and are cleared only by a full panel
re-init (which is why niri's modeset used to make them disappear).

So: after the synchronous touch reload in hx83102_enable(), re-send the panel
init sequence.  Touch stays alive (its firmware was just loaded) and the display
is repaired immediately instead of waiting for the next modeset.
"""
import os
import sys

PN = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c')

p = open(PN, encoding='utf-8').read()

OLD = """	/*
	 * The panel DSI init sequence knocks the touch side of this TDDI out of
	 * scanning mode.  The hook below only re-sends the 4 restore commands --
	 * no firmware reload, because that bulk SPI write is what corrupts the
	 * display while the panel is scanning.
	 */
	if (nvt_ts_panel_event)
		nvt_ts_panel_event(true);

	return 0;
}"""

NEW = """	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	/*
	 * The Novatek TDDI needs its firmware reloaded after the panel is
	 * (re)initialised, and that download disturbs the panel's display state
	 * (stripes starting around the first NVT activity).  Re-sending the panel
	 * init sequence right afterwards repairs the display, which is why a
	 * modeset was the only thing that used to clear the stripes.
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

if NEW in p:
    print('already patched')
    sys.exit(0)
if OLD not in p:
    sys.exit('enable() body not recognised')
p = p.replace(OLD, NEW, 1)
open(PN, 'w', encoding='utf-8', newline='\n').write(p)
print('enable(): touch reload followed by panel re-init')

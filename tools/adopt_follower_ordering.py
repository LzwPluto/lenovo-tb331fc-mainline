#!/usr/bin/env python3
"""adopt_panel_follower_ordering.py

Adopt the ordering used by the mainline NT36523 work (Jianhua Lu / sm8150-mainline,
sm8250-mainline, and the "novatek-nvt-ts as panel follower" patch):

    prepare():  register init + DSC PPS, but DO NOT send 0x11 (sleep out) / 0x29
                (display on) yet.
    follower / panel_prepared:
                download the touch firmware -- the panel is still asleep here,
                so the TDDI MCU reflash cannot disturb any displayed content.
    enable():   send 0x11 -> 0x29, then turn the backlight on.

Our port sent 0x29 at the end of prepare(), so by the time the touch hook ran in
enable() the panel was already scanning -> stripes.

Also drop the probe-time delayed firmware work (2500 ms) which fired at ~13 s with
the display up; the download now happens only from the panel hook.
"""
import os
import sys

BASE = os.path.expanduser('~/kbuild/linux-next-tb128fu-hx83102-panel-port')
PN = os.path.join(BASE, 'drivers/gpu/drm/panel/panel-himax-hx83102.c')
TS = os.path.join(BASE, 'drivers/input/touchscreen/nt36523_ts.c')

# ============ 1. panel init: do not send 0x11 / 0x29 ============
p = open(PN, encoding='utf-8').read()

OLD_INIT = """	/* sleep out + display on (+ anything after) */
	return p255_inx_replay_range(ctx, p255_inx_on_seq,
				     sizeof(p255_inx_on_seq), &pos, false);
}"""
NEW_INIT = """	if (ctx->desc->has_dsc) {
		/*
		 * 0x11 (sleep out) and 0x29 (display on) are deliberately NOT sent
		 * here: hx83102_enable() sends them after the touch firmware
		 * download, so the panel is still asleep (not scanning) while the
		 * TDDI reflashes its MCU.  This is the ordering used by the
		 * mainline NT36523 panel/follower work.
		 */
		return 0;
	}

	/* non-DSC panels keep the original behaviour */
	return p255_inx_replay_range(ctx, p255_inx_on_seq,
				     sizeof(p255_inx_on_seq), &pos, false);
}"""
if OLD_INIT not in p:
    sys.exit('lenovo_p255_inx_init tail not recognised')
p = p.replace(OLD_INIT, NEW_INIT, 1)
print('init(): 0x11/0x29 deferred to enable()')

# ============ 2. enable(): wait for touch, download while asleep, then 0x11/0x29 ============
OLD_EN = """	msleep(130);

	if (ctx->backlight)
		backlight_update_status(ctx->backlight);

	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

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

NEW_EN = """	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	msleep(130);

	if (ctx->desc->has_dsc) {
		int i;

		/* The touch driver may probe after this panel; wait for it so the
		 * firmware download below can actually happen. */
		if (&nvt_fw_ready != NULL) {
			for (i = 0; i < 300 && !nvt_fw_ready; i++)
				msleep(50);
		}

		/*
		 * Panel is still asleep (no 0x11/0x29 yet) -> the TDDI MCU reflash
		 * cannot disturb displayed content.
		 */
		if (nvt_ts_panel_event)
			nvt_ts_panel_event(true);

		mipi_dsi_dcs_exit_sleep_mode_multi(&dsi_ctx);   /* 0x11 */
		mipi_dsi_msleep(&dsi_ctx, 120);
		mipi_dsi_dcs_set_display_on_multi(&dsi_ctx);    /* 0x29 */
		if (dsi_ctx.accum_err)
			return dsi_ctx.accum_err;
	}

	if (ctx->backlight)
		backlight_update_status(ctx->backlight);

	return 0;
}"""
if OLD_EN not in p:
    sys.exit('enable() body not recognised')
p = p.replace(OLD_EN, NEW_EN, 1)
print('enable(): wait touch -> download (asleep) -> 0x11/0x29 -> backlight')
open(PN, 'w', encoding='utf-8', newline='\n').write(p)

# ============ 3. touch driver: no probe-time download; flag = driver up ============
t = open(TS, encoding='utf-8').read()

OLD_Q = '\tqueue_delayed_work(nvt_fwu_wq, &ts->nvt_fwu_work, msecs_to_jiffies(2500));'
NEW_Q = ('\t/*\n'
         '\t * No probe-time download: it used to run ~13 s in, while the panel was\n'
         '\t * already scanning, which is exactly when the stripes appeared.  The\n'
         '\t * panel driver now calls nvt_ts_panel_event() from its enable() while the\n'
         '\t * panel is still asleep.\n'
         '\t */')
if OLD_Q in t:
    t = t.replace(OLD_Q, NEW_Q, 1)
    print('probe: 2500 ms firmware work removed')
else:
    print('probe: firmware work already removed')

if 'extern bool nvt_fw_ready;' not in t:
    t = t.replace('uint32_t SWRST_N8_ADDR = 0; //read from dtsi',
                  'uint32_t SWRST_N8_ADDR = 0; //read from dtsi\n'
                  'extern bool nvt_fw_ready;   /* "touch driver is up" for the panel driver */', 1)
    print('extern nvt_fw_ready declared')

# set the flag at the end of probe
if 'nvt_fw_ready = true;' not in t:
    OLD_END = '\tNVT_LOG("end\\n");'
    NEW_END = ('\tNVT_LOG("end\\n");\n'
               '\n'
               '\t/* let the panel driver proceed and download the firmware while it is\n'
               '\t * still asleep */\n'
               '\tnvt_fw_ready = true;')
    if OLD_END in t:
        t = t.replace(OLD_END, NEW_END, 1)
        print('probe: nvt_fw_ready set (driver up)')
    else:
        print('WARNING: could not set nvt_fw_ready in probe')
open(TS, 'w', encoding='utf-8', newline='\n').write(t)

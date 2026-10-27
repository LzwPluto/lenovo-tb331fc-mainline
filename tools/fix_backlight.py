#!/usr/bin/env python3
"""fix_backlight.py

Two real bugs + one timing fix in panel-himax-hx83102.c:

BUG 1 (brightness never changes)
    if (ctx->desc->inverted_dbv)
        brightness = 4095 - brightness;         /* wrong */
  Qualcomm's qcom,mdss-dsi-bl-inverted-dbv means the DBV *byte order* is
  inverted, i.e. a swab16:
        bl_lvl = ((bl_lvl & 0xFF) << 8) | (bl_lvl >> 8);
  With "4095 - v" the panel receives the bytes in the wrong order, reads a huge
  value and clamps to max -> the slider appears to do nothing.

BUG 2 (half screen solid white + dsi_err_worker status=5)
  GNOME sends one backlight update per slider event (dozens..hundreds per
  second). Each one issues a DCS 0x51 while the 90 Hz DSC video stream is
  running; dsi_wait4video_eng_busy() cannot find a BLLP window and the command
  DMA collides with the pixel stream -> FIFO underflow + timeout -> the DSC
  decoder of the second slice desyncs -> right half decodes to all ones (white).
  Fix: coalesce updates in a delayed work (last value wins, ~60 ms) so at most
  ~16 DCS writes per second are issued.

TIMING FIX
  The initial brightness used to be written after 0x29 (video stream already
  active).  Send it before 0x11/0x29 instead: the panel is still in sleep mode,
  so the DCS write cannot collide with anything.
"""
import os
import sys

P = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c')

s = open(P, encoding='utf-8').read()

if 'hx83102_bl_work' in s:
    print('already patched')
    sys.exit(0)

# ---------------- 1. struct fields ----------------
OLD_STRUCT = """	struct backlight_device *backlight;
	struct drm_dsc_config dsc;
};"""
NEW_STRUCT = """	struct backlight_device *backlight;
	struct drm_dsc_config dsc;
	/* backlight write coalescing: one DCS 0x51 per ~60 ms at most */
	struct delayed_work bl_work;
	u16 bl_val;
};"""
if OLD_STRUCT not in s:
    sys.exit('struct anchor not found')
s = s.replace(OLD_STRUCT, NEW_STRUCT, 1)

# ---------------- 2. backlight implementation ----------------
OLD_BL = """static int hx83102_bl_update_status(struct backlight_device *bl)
{
	struct hx83102 *ctx = bl_get_data(bl);
	u16 brightness = backlight_get_brightness(bl);

	/* TB331FC: Hardware uses inverted DBV scale (qcom,mdss-dsi-bl-inverted-dbv).
	 * In addition, keep MIPI_DSI_MODE_LPM untouched to prevent High-Speed DMA
	 * collisions during active video mode streaming (which causes black stripes
	 * and DSI FIFO underflow).
	 */
	if (ctx->desc->inverted_dbv) {
		if (brightness > 4095)
			brightness = 4095;
		brightness = 4095 - brightness;
	}

	return mipi_dsi_dcs_set_display_brightness_large(ctx->dsi, brightness);
}
"""

NEW_BL = """/*
 * Write DCS 0x51 right now.  Only safe when the video stream is not running
 * (before 0x11/0x29) or from the coalescing work below.
 */
static int hx83102_bl_write(struct hx83102 *ctx, u16 brightness)
{
	if (brightness > 4095)
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
}

static void hx83102_bl_work(struct work_struct *work)
{
	struct hx83102 *ctx = container_of(work, struct hx83102, bl_work.work);

	hx83102_bl_write(ctx, ctx->bl_val);
}

static int hx83102_bl_update_status(struct backlight_device *bl)
{
	struct hx83102 *ctx = bl_get_data(bl);

	/*
	 * Coalesce updates: a slider drag generates one call per event, and each
	 * DCS 0x51 issued while the 90 Hz DSC video stream runs can collide with
	 * the pixel stream (dsi_err_worker status=5) and desync the second DSC
	 * slice -> right half of the panel turns solid white.
	 */
	ctx->bl_val = backlight_get_brightness(bl);
	mod_delayed_work(system_wq, &ctx->bl_work, msecs_to_jiffies(60));

	return 0;
}
"""
if OLD_BL not in s:
    sys.exit('backlight function not recognised')
s = s.replace(OLD_BL, NEW_BL, 1)

# ---------------- 3. init the work in probe ----------------
OLD_PROBE = '		ctx->backlight = hx83102_backlight_register(ctx);'
NEW_PROBE = ('		INIT_DELAYED_WORK(&ctx->bl_work, hx83102_bl_work);\n'
             '		ctx->backlight = hx83102_backlight_register(ctx);')
if OLD_PROBE not in s:
    sys.exit('backlight register anchor not found')
s = s.replace(OLD_PROBE, NEW_PROBE, 1)

# ---------------- 4. enable(): brightness before 0x11 ----------------
OLD_EN = """		if (nvt_ts_panel_event)
			nvt_ts_panel_event(true);

		mipi_dsi_dcs_exit_sleep_mode_multi(&dsi_ctx);   /* 0x11 */"""
NEW_EN = """		if (nvt_ts_panel_event)
			nvt_ts_panel_event(true);

		/*
		 * Program the initial brightness *before* 0x11/0x29: the panel is
		 * still asleep, so the DCS 0x51 cannot collide with the video
		 * stream (it did when it was written after 0x29).
		 */
		if (ctx->backlight)
			hx83102_bl_write(ctx,
					 backlight_get_brightness(ctx->backlight));

		mipi_dsi_dcs_exit_sleep_mode_multi(&dsi_ctx);   /* 0x11 */"""
if OLD_EN not in s:
    sys.exit('enable() anchor not found')
s = s.replace(OLD_EN, NEW_EN, 1)

# remove the now-redundant update after 0x29
OLD_EN2 = """	if (ctx->backlight)
		backlight_update_status(ctx->backlight);

	return 0;
}

static int hx83102_disable(struct drm_panel *panel)"""
NEW_EN2 = """	return 0;
}

static int hx83102_disable(struct drm_panel *panel)"""
if OLD_EN2 in s:
    s = s.replace(OLD_EN2, NEW_EN2, 1)
    print('removed redundant post-0x29 backlight write')
else:
    print('note: post-0x29 backlight call not found (ok)')

# ---------------- 5. cancel the work when the panel goes down ----------------
OLD_DIS = """	if (nvt_ts_panel_event)
		nvt_ts_panel_event(false);

	dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;"""
NEW_DIS = """	cancel_delayed_work_sync(&ctx->bl_work);

	if (nvt_ts_panel_event)
		nvt_ts_panel_event(false);

	dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;"""
if OLD_DIS not in s:
    sys.exit('disable() anchor not found')
s = s.replace(OLD_DIS, NEW_DIS, 1)

open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('patched: byte-swap DBV + 60 ms coalescing + brightness before 0x11')

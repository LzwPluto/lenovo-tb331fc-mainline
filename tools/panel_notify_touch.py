#!/usr/bin/env python3
"""panel_notify_touch.py

Evidence: on Android the vendor touch module is a *holder* of panel_event_notifier:

    /sys/module/panel_event_notifier/holders/nvt36523_spi

and Android's log shows the chain

    nvt_panel_notifier_callback: resume notification pre commit
    nvt_ts_resume: start ... end

i.e. the touch controller is (re)initialised when the panel comes up.  Our
mainline driver initialises it at probe time - before the panel is even on - and
then nothing ever tells it "display is up", so it never starts scanning.

Implement the same chain without Qualcomm's notifier: the panel driver calls a
weak symbol exported by the touch driver.

  panel hx83102_enable()  -> nvt_ts_panel_event(true)   (display on)
  panel hx83102_disable() -> nvt_ts_panel_event(false)  (display off)

On "on" the touch driver runs the vendor's resume sequence: firmware download
(into the controller's SRAM - no storage wear) + scan-enable commands.
"""
import sys

PANEL = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c'
TOUCH = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'

# ---------------- touch side ----------------
s = open(TOUCH, encoding='utf-8').read()
if 'nvt_ts_panel_event' in s:
    print('touch: already patched')
else:
    # insert the worker + exported hook just before the probe function
    anchor = 'static int32_t nvt_ts_probe(struct spi_device *client)'
    if anchor not in s:
        # find actual probe signature
        import re
        m = re.search(r'^static int32_t nvt_ts_probe\(.*$', s, re.M)
        if not m:
            sys.exit('probe signature not found')
        anchor = m.group(0)

    code = '''/*******************************************************
 Panel event hook (called by the display driver)

 Mirrors the vendor driver, which registers with panel_event_notifier and
 re-initialises the controller whenever the panel comes up.
*******************************************************/
static void nvt_panel_on_work(struct work_struct *work)
{
	if (!ts || !ts->client)
		return;

	NVT_LOG("panel on -> re-init touch\\n");
	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_check_fw_reset_state(RESET_STATE_REK);
	mutex_unlock(&ts->lock);
	nvt_restore_cmd_func();
}

static DECLARE_WORK(nvt_panel_work, nvt_panel_on_work);

void nvt_ts_panel_event(bool on)
{
	if (!ts)
		return;

	if (on)
		schedule_work(&nvt_panel_work);
}
EXPORT_SYMBOL_GPL(nvt_ts_panel_event);

'''
    s = s.replace(anchor, code + anchor, 1)
    open(TOUCH, 'w', encoding='utf-8', newline='\n').write(s)
    print('touch: exported nvt_ts_panel_event()')

# ---------------- panel side ----------------
p = open(PANEL, encoding='utf-8').read()
if 'nvt_ts_panel_event' in p:
    print('panel: already patched')
else:
    # weak declaration near the top (after the last #include)
    lines = p.split('\n')
    last_inc = max(i for i, l in enumerate(lines) if l.startswith('#include'))
    decl = ('\n/*\n * The Novatek touch controller on this tablet is only brought into\n'
            ' * active scanning mode once the panel is up, exactly like the vendor\n'
            ' * driver does via panel_event_notifier.  Weak symbol so this panel\n'
            ' * driver still links when the touch driver is not built in.\n */\n'
            'extern void nvt_ts_panel_event(bool on) __attribute__((weak));\n')
    lines.insert(last_inc + 1, decl)
    p = '\n'.join(lines)

    # call at the end of enable()
    old_en = '''	if (ctx->backlight)
		backlight_update_status(ctx->backlight);

	return 0;
}'''
    new_en = '''	if (ctx->backlight)
		backlight_update_status(ctx->backlight);

	/* panel is up: let the touch controller start scanning */
	if (nvt_ts_panel_event)
		nvt_ts_panel_event(true);

	return 0;
}'''
    if old_en not in p:
        sys.exit('enable() anchor not found')
    p = p.replace(old_en, new_en, 1)

    # call at the start of disable()
    old_dis = '''	dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;

	mipi_dsi_dcs_set_display_off_multi(&dsi_ctx);'''
    new_dis = '''	if (nvt_ts_panel_event)
		nvt_ts_panel_event(false);

	dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;

	mipi_dsi_dcs_set_display_off_multi(&dsi_ctx);'''
    if old_dis not in p:
        sys.exit('disable() anchor not found')
    p = p.replace(old_dis, new_dis, 1)

    open(PANEL, 'w', encoding='utf-8', newline='\n').write(p)
    print('panel: calls nvt_ts_panel_event() from enable/disable')

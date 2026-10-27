# fix_touch_probe.py
p_panel = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c'
t = open(p_panel).read()
t = t.replace('for (i = 0; i < 300 && !nvt_fw_ready; i++)', 'for (i = 0; i < 700 && !nvt_fw_ready; i++)')
open(p_panel, 'w').write(t)
print('panel: updated timeout to 700 iterations (35s)')

p_ts = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
t = open(p_ts).read()
old_code = '''\
#if defined(CONFIG_FB)
	ts->fb_notif.notifier_call = nvt_fb_notifier_callback;
	fb_register_client(&ts->fb_notif);
#endif
	nvt_restore_cmd_func();
	bTouchIsAwake = 1;
	NVT_LOG("end\\n");

	/* let the panel driver proceed and download the firmware while it is
	 * still asleep */
	nvt_fw_ready = true;

	nvt_irq_enable(true);'''

new_code = '''\
#if defined(CONFIG_FB)
	ts->fb_notif.notifier_call = nvt_fb_notifier_callback;
	fb_register_client(&ts->fb_notif);
#endif
	/* Always perform initial firmware flash and setup in probe */
	nvt_panel_on_work(NULL);
	bTouchIsAwake = 1;
	NVT_LOG("end\\n");

	nvt_fw_ready = true;'''

if old_code in t:
    t = t.replace(old_code, new_code)
    open(p_ts, 'w').write(t)
    print('ts: probe now calls nvt_panel_on_work(NULL)')
else:
    print('ts: old_code not matched!')

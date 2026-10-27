#!/usr/bin/env python3
"""nvt_fb_notifier.py

Key observation on hardware: touch only ever works in the window where the
display subsystem finishes initialising (Niri/DRM modeset at ~25-32 s).  The
vendor driver hooks the panel with nvt_panel_notifier_callback and re-initialises
the controller from there; our driver initialises the controller at probe time,
long before the panel is on, and then the panel bring-up leaves it dead.

Add a framebuffer notifier: when fbdev registers / the mode changes / the display
resumes, request a touch re-initialisation (firmware + commands).  The request is
serviced by the existing 100 ms watchdog work, so no new workqueue is needed.
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

if 'nvt_fb_notifier_callback' in s:
    print('fb notifier already present')
    sys.exit(0)

# 1) add the request flag + notifier callback right before the watchdog function
anchor = 'static unsigned long nvt_last_touch_jiffies;   /* updated by the event handler */'
if anchor not in s:
    sys.exit('watchdog anchor not found')

cb = '''static int nvt_reinit_req;

#if defined(CONFIG_FB)
static int nvt_fb_notifier_callback(struct notifier_block *self,
				    unsigned long event, void *data)
{
	struct fb_event *evdata = data;
	int blank;

	if (event != FB_EVENT_BLANK && event != FB_EVENT_MODE_CHANGE &&
	    event != FB_EVENT_FB_REGISTERED)
		return 0;

	if (event == FB_EVENT_BLANK && evdata && evdata->data) {
		blank = *(int *)evdata->data;
		if (blank != FB_BLANK_UNBLANK)
			return 0;
	}

	/* 面板已初始化/已解除空白 —— 请求重新初始化触摸 */
	nvt_reinit_req = 1;
	return 0;
}

static struct notifier_block nvt_fb_notif = {
	.notifier_call = nvt_fb_notifier_callback,
};
#endif

'''
s = s.replace(anchor, cb + anchor, 1)

# 2) service the request inside the watchdog, before the idle heuristics
w_anchor = '\tif (!nvt_last_touch_jiffies)\n\t\tnvt_last_touch_jiffies = jiffies;'
if w_anchor not in s:
    sys.exit('watchdog body anchor not found')

service = '''	if (nvt_reinit_req) {
		nvt_reinit_req = 0;
		NVT_LOG("display ready -> re-init touch\\n");
		mutex_lock(&ts_hb->lock);
		nvt_update_firmware(ts_hb->fw_name);
		nvt_check_fw_reset_state(RESET_STATE_REK);
		mutex_unlock(&ts_hb->lock);
		nvt_restore_cmd_func();
		nvt_last_touch_jiffies = jiffies;
		nvt_heal_stage = 0;
	}

''' + w_anchor
s = s.replace(w_anchor, service, 1)

# 3) register the notifier at the end of probe
reg_anchor = '\tnvt_restore_cmd_func();\n\tbTouchIsAwake = 1;'
if reg_anchor not in s:
    sys.exit('probe end anchor not found')
s = s.replace(reg_anchor, '''#if defined(CONFIG_FB)
	ts->fb_notif.notifier_call = nvt_fb_notifier_callback;
	fb_register_client(&ts->fb_notif);
#endif
	nvt_restore_cmd_func();
	bTouchIsAwake = 1;''', 1)

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('fb notifier added: touch is re-initialised when the display comes up')

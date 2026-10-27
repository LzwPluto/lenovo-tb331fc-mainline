#!/usr/bin/env python3
"""nvt_continuous_selfheal.py

The fb notifier never fires on this stack (Niri drives DRM directly, so there is
no fbdev mode change), so use continuous self-healing instead of a one-shot
escalation:

  idle > 2 s  AND last cmd  > 2 s ago  -> re-send the scan-enable commands
  idle > 8 s  AND last flash > 8 s ago -> re-download firmware + commands

Any valid touch packet refreshes the idle timer.  The effect: whenever the user
leaves the panel alone for a moment, the controller is re-armed, so the next
touch lands on a freshly initialised chip.
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

start = s.find('static void nvt_hb_work_func(struct work_struct *work)')
if start < 0:
    sys.exit('watchdog not found')
end = s.find('\n}\n', start)

new = '''static void nvt_hb_work_func(struct work_struct *work)
{
	struct nvt_ts_data *ts_hb =
		container_of(work, struct nvt_ts_data, nvt_hb_work.work);
	static unsigned long last_cmd, last_flash;
	static int last_lvl = -1;
	unsigned int idle_ms, since_cmd, since_flash;
	int lvl;

	if (!ts_hb || !ts_hb->client || !bTouchIsAwake) {
		queue_delayed_work(ts_hb->event_wq ? ts_hb->event_wq : system_wq,
				   &ts_hb->nvt_hb_work, msecs_to_jiffies(100));
		return;
	}

	lvl = gpio_get_value(ts_hb->irq_gpio);
	if (lvl != last_lvl) {
		NVT_LOG("HB int=%d (changed)\\n", lvl);
		last_lvl = lvl;
	}

	if (!nvt_last_touch_jiffies)
		nvt_last_touch_jiffies = jiffies;
	if (!last_cmd)
		last_cmd = jiffies;
	if (!last_flash)
		last_flash = jiffies;

	idle_ms    = jiffies_to_msecs(jiffies - nvt_last_touch_jiffies);
	since_cmd  = jiffies_to_msecs(jiffies - last_cmd);
	since_flash= jiffies_to_msecs(jiffies - last_flash);

	/* 空闲 8 秒以上：重刷固件（较慢但彻底） */
	if (idle_ms > 8000 && since_flash > 8000) {
		NVT_LOG("selfheal: re-download firmware (idle %u ms)\\n", idle_ms);
		mutex_lock(&ts_hb->lock);
		nvt_update_firmware(ts_hb->fw_name);
		nvt_check_fw_reset_state(RESET_STATE_REK);
		mutex_unlock(&ts_hb->lock);
		nvt_restore_cmd_func();
		last_flash = jiffies;
		last_cmd = jiffies;
	}
	/* 空闲 2 秒以上：只重发扫描命令（很便宜） */
	else if (idle_ms > 2000 && since_cmd > 2000) {
		NVT_LOG("selfheal: re-send scan commands (idle %u ms)\\n", idle_ms);
		nvt_restore_cmd_func();
		last_cmd = jiffies;
	}

	queue_delayed_work(ts_hb->event_wq ? ts_hb->event_wq : system_wq,
			   &ts_hb->nvt_hb_work, msecs_to_jiffies(100));
}
'''

s = s[:start] + new + s[end + 3:]
open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('continuous self-heal installed (2 s commands / 8 s firmware, repeating)')

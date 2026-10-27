#!/usr/bin/env python3
"""nvt_selfheal_watchdog.py

Facts gathered on hardware:
  * the controller answers SPI and reports healthy firmware (PID 6072, fw 0x0F)
  * it produces one full gesture burst and then stops asserting INT entirely
  * the vendor driver calls nvt_update_firmware() from inside its work handler,
    i.e. it recovers the controller on the fly
  * the stock ESD watchdog (1.5 s) effectively did the same thing

So implement an escalating self-heal watchdog (100 ms tick):
  idle < 2 s          -> nothing
  2 s .. 6 s idle     -> re-send the scan-enable commands (cheap: 4 spi writes)
  > 6 s idle          -> re-download the firmware + re-send the commands
Any valid touch packet resets the timer.
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

start = s.find('static void nvt_hb_work_func(struct work_struct *work)')
if start < 0:
    sys.exit('heartbeat not found')
end = s.find('\n}\n', start)

new = '''static unsigned long nvt_last_touch_jiffies;   /* updated by the event handler */
static int nvt_heal_stage;

static void nvt_hb_work_func(struct work_struct *work)
{
	struct nvt_ts_data *ts_hb =
		container_of(work, struct nvt_ts_data, nvt_hb_work.work);
	static int last_lvl = -1;
	unsigned int idle_ms;
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

	idle_ms = jiffies_to_msecs(jiffies - nvt_last_touch_jiffies);

	/* 空闲 2 秒：重新下发扫描使能命令（便宜） */
	if (idle_ms > 2000 && nvt_heal_stage < 1) {
		NVT_LOG("selfheal: re-send scan commands (idle %u ms)\\n", idle_ms);
		nvt_restore_cmd_func();
		nvt_heal_stage = 1;
	}

	/* 空闲 6 秒：重刷固件（贵，但能恢复） */
	if (idle_ms > 6000 && nvt_heal_stage < 2) {
		NVT_LOG("selfheal: re-download firmware (idle %u ms)\\n", idle_ms);
		mutex_lock(&ts_hb->lock);
		nvt_update_firmware(ts_hb->fw_name);
		nvt_get_fw_info();
		mutex_unlock(&ts_hb->lock);
		nvt_restore_cmd_func();
		nvt_heal_stage = 2;
	}

	queue_delayed_work(ts_hb->event_wq ? ts_hb->event_wq : system_wq,
			   &ts_hb->nvt_hb_work, msecs_to_jiffies(100));
}
'''

s = s[:start] + new + s[end + 3:]

# reset the idle timer whenever a real touch packet is parsed, and reset stage
anchor = '\tinput_report_key(ts->input_dev, BTN_TOUCH, (finger_cnt > 0));'
if anchor not in s:
    sys.exit('report anchor not found')
s = s.replace(anchor,
              '\tnvt_last_touch_jiffies = jiffies;\n\tnvt_heal_stage = 0;\n' + anchor, 1)

# forward declarations
if 'static unsigned long nvt_last_touch_jiffies;' not in s.split('static void nvt_hb_work_func')[0]:
    decl = ('extern int32_t nvt_restore_cmd_func(void);\n'
            'extern int32_t nvt_update_firmware(const char *fw_name);\n\n')
    s = s.replace('static unsigned long nvt_last_touch_jiffies;   /* updated by the event handler */',
                  decl + 'static unsigned long nvt_last_touch_jiffies;   /* updated by the event handler */', 1)

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('self-heal watchdog installed (2 s re-send commands, 6 s re-flash firmware)')

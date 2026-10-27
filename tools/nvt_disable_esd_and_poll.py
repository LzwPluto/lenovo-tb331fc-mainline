#!/usr/bin/env python3
"""nvt_disable_esd_and_poll.py

Two changes:

1. NVT_TOUCH_ESD_PROTECT 1 -> 0
   The ESD watchdog fires when no touch interrupt has been seen for 1500 ms and
   then re-downloads the whole firmware.  On this controller that is exactly the
   "works for a moment, then dies" pattern, so rule it out.

2. Remove the 5 ms polling fallback (it made things worse: 200 Hz event-buffer
   reads returned only stale release packets and the chip stopped producing real
   touches).  Back to IRQ-driven handling, with the heartbeat only sampling the
   INT line every 100 ms.
"""
import re
import sys

HDR = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523.h'
SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'

h = open(HDR, encoding='utf-8').read()
if '#define NVT_TOUCH_ESD_PROTECT 1' in h:
    h = h.replace('#define NVT_TOUCH_ESD_PROTECT 1',
                  '#define NVT_TOUCH_ESD_PROTECT 0  /* ESD watchdog re-downloads fw every 1.5 s idle - disabled */')
    open(HDR, 'w', encoding='utf-8', newline='\n').write(h)
    print('header: ESD protection disabled')
else:
    print('header: ESD already changed')

s = open(SRC, encoding='utf-8').read()

start = s.find('static void nvt_hb_work_func(struct work_struct *work)')
if start < 0:
    sys.exit('heartbeat not found')
end = s.find('\n}\n', start)

new = '''static void nvt_hb_work_func(struct work_struct *work)
{
	struct nvt_ts_data *ts_hb =
		container_of(work, struct nvt_ts_data, nvt_hb_work.work);
	static int last_lvl = -1;
	int lvl;

	if (!ts_hb || !ts_hb->client)
		return;

	/* INT 电平诊断：只读 GPIO，不碰 SPI 总线（轮询已验证有害） */
	lvl = gpio_get_value(ts_hb->irq_gpio);
	if (lvl != last_lvl) {
		NVT_LOG("HB int=%d (changed)\\n", lvl);
		last_lvl = lvl;
	}

	queue_delayed_work(ts_hb->event_wq ? ts_hb->event_wq : system_wq,
			   &ts_hb->nvt_hb_work, msecs_to_jiffies(100));
}
'''

s = s[:start] + new + s[end + 3:]
s = s.replace('&ts->nvt_hb_work, msecs_to_jiffies(5));',
              '&ts->nvt_hb_work, msecs_to_jiffies(100));')
s = s.replace('NVT_LOG("poll fallback started (5ms)\\n");',
              'NVT_LOG("int-level watch started (100ms)\\n");')
open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('source: polling removed, INT watch at 100 ms')

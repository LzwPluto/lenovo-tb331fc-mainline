#!/usr/bin/env python3
"""nvt_poll_fallback.py

Symptom: touch produces one burst of interrupts at boot and then dies.  The INT
line sits at its idle level, the chip answers SPI reads, but no further edges
arrive, so an edge-triggered IRQ never fires again.

Fix: keep the IRQ path, but add a 5 ms polling fallback that calls the very same
nvt_ts_work_func().  That handler already:
  * takes ts->lock,
  * reads the 109-byte event packet,
  * bails out on the idle packet (0xFF 0x00 / all 0x77), and
  * reports real touches and releases.
So an idle poll reads an "empty" packet and reports nothing -> no ghost touches,
while a real touch is picked up within 5 ms even if the IRQ is dead.
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

start = s.find('static void nvt_hb_work_func(struct work_struct *work)')
if start < 0:
    sys.exit('heartbeat function not found')
end = s.find('\n}\n', start)
if end < 0:
    sys.exit('function end not found')

new = '''static void nvt_hb_work_func(struct work_struct *work)
{
	struct nvt_ts_data *ts_hb =
		container_of(work, struct nvt_ts_data, nvt_hb_work.work);
	static int last_lvl = -1;
	static unsigned long polls;
	int lvl;

	if (!ts_hb || !ts_hb->client)
		return;

	if (!bTouchIsAwake) {
		queue_delayed_work(ts_hb->event_wq ? ts_hb->event_wq : system_wq,
				   &ts_hb->nvt_hb_work, msecs_to_jiffies(5));
		return;
	}

	lvl = gpio_get_value(ts_hb->irq_gpio);
	if (lvl != last_lvl) {
		NVT_LOG("HB int=%d (changed)\\n", lvl);
		last_lvl = lvl;
	}

	/*
	 * Polling fallback: the IRQ only delivers one burst on this controller.
	 * nvt_ts_work_func() reads the event packet and ignores empty ones, so
	 * this is safe to run unconditionally.
	 */
	nvt_ts_work_func(0, ts_hb);
	polls++;

	queue_delayed_work(ts_hb->event_wq ? ts_hb->event_wq : system_wq,
			   &ts_hb->nvt_hb_work, msecs_to_jiffies(5));
}
'''

s = s[:start] + new + s[end + 3:]

# nvt_ts_work_func is defined after the heartbeat -> add a forward declaration
if 'static irqreturn_t nvt_hb_fwd;' not in s and 'irqreturn_t nvt_ts_work_func(int irq, void *data);' not in s:
    anchor = 'static void nvt_hb_work_func(struct work_struct *work)'
    s = s.replace(anchor,
                  'irqreturn_t nvt_ts_work_func(int irq, void *data);\n\n' + anchor, 1)

# heartbeat period 100 -> 5 ms
s = s.replace('&ts->nvt_hb_work, msecs_to_jiffies(500));',
              '&ts->nvt_hb_work, msecs_to_jiffies(5));')
s = s.replace('NVT_LOG("heartbeat started (500ms)\\n");',
              'NVT_LOG("poll fallback started (5ms)\\n");')

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('polling fallback installed (5 ms, reuses nvt_ts_work_func)')

#!/usr/bin/env python3
"""fix_nvt_heartbeat.py

v1 of the heartbeat did an 8-byte SPI read of EVENT_BUF every 500 ms.  If the
controller's event buffer is read-and-clear (typical for Novatek), that read
steals touch packets from the real handler and can also leave a partially
consumed buffer behind - which would explain "commands succeed but no touch data
ever arrives".

v2: never touch the SPI bus.  Only sample the INT GPIO level and log changes.
That keeps the diagnostic value (is the chip asserting INT?) with zero
interference.
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

start = s.find('static void nvt_hb_work_func(struct work_struct *work)')
if start < 0:
    sys.exit('heartbeat function not found')
# find end of function: the closing brace at column 0 after start
end = s.find('\n}\n', start)
if end < 0:
    sys.exit('function end not found')

new = '''static void nvt_hb_work_func(struct work_struct *work)
{
	struct nvt_ts_data *ts_hb =
		container_of(work, struct nvt_ts_data, nvt_hb_work.work);
	static int last_lvl = -1;
	int lvl;

	if (!ts_hb || !ts_hb->client)
		return;

	/* 只采样 INT 电平，绝不碰 SPI 总线 —— 避免偷走触摸数据 */
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
open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('heartbeat v2: INT-level only, 100 ms, no SPI access')

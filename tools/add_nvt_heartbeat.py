#!/usr/bin/env python3
"""add_nvt_heartbeat.py

Purpose: figure out (and maybe fix) why NT36523 stops asserting INT after the
first touch/release cycle.

Adds a 500 ms delayed work that
  * logs the current INT GPIO level (0 = low, 1 = high), and
  * performs a small SPI read of EVENT_BUF (a "dummy" read).

Two outcomes are informative:
  * INT stays 0 and the buffer keeps the last packet -> the chip stopped
    scanning; it needs a keep-alive (which this dummy read may provide).
  * INT goes 1 on touch -> the chip is fine and only the IRQ delivery is broken.

The dummy read may itself keep the controller awake, so this doubles as a
candidate fix.

Idempotent: does nothing if the heartbeat is already present.
"""
import re
import sys

HDR = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523.h'
SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'

# ---------- 1) add the delayed_work field to struct nvt_ts_data ----------
h = open(HDR, encoding='utf-8').read()
if 'nvt_hb_work' not in h:
    anchor = '\tstruct delayed_work nvt_fwu_work;'
    if anchor not in h:
        sys.exit('anchor not found in header')
    h = h.replace(anchor, anchor + '\n\tstruct delayed_work nvt_hb_work;', 1)
    open(HDR, 'w', encoding='utf-8', newline='\n').write(h)
    print('header: added nvt_hb_work field')
else:
    print('header: already patched')

# ---------- 2) add the heartbeat function + scheduling ----------
s = open(SRC, encoding='utf-8').read()
if 'nvt_hb_work_func' in s:
    print('source: already patched')
    sys.exit(0)

func = r'''
/*******************************************************
 NT36523 heartbeat / INT diagnostic

 Runs every 500 ms: logs the INT GPIO level and performs a small dummy SPI read
 of the event buffer.  Used to tell "chip stopped scanning" apart from
 "IRQ delivery broken", and as a keep-alive in case the controller dozes off.
*******************************************************/
static void nvt_hb_work_func(struct work_struct *work)
{
	struct nvt_ts_data *ts_hb =
		container_of(work, struct nvt_ts_data, nvt_hb_work.work);
	int lvl;
	uint8_t buf[8] = {0};
	int32_t ret;

	if (!ts_hb || !ts_hb->client)
		return;

	lvl = gpio_get_value(ts_hb->irq_gpio);

	mutex_lock(&ts_hb->lock);
	nvt_set_page(ts_hb->mmap->EVENT_BUF_ADDR);
	buf[0] = (ts_hb->mmap->EVENT_BUF_ADDR) & 0x7F;
	ret = CTP_SPI_READ(ts_hb->client, buf, 8);
	mutex_unlock(&ts_hb->lock);

	if (ret < 0)
		NVT_ERR("HB int=%d spi_read=%d\n", lvl, ret);
	else
		NVT_LOG("HB int=%d buf=%02X %02X %02X %02X %02X %02X %02X\n",
			lvl, buf[1], buf[2], buf[3], buf[4], buf[5], buf[6], buf[7]);

	queue_delayed_work(ts_hb->event_wq ? ts_hb->event_wq : system_wq,
			   &ts_hb->nvt_hb_work, msecs_to_jiffies(500));
}

'''

# insert the function right before nvt_ts_work_func definition
m = re.search(r'\nirqreturn_t nvt_ts_work_func\(int irq, void \*data\)', s)
if not m:
    sys.exit('nvt_ts_work_func definition not found')
s = s[:m.start()] + func + s[m.start() + 1:]

# schedule it after the IRQ is successfully requested
anchor = '''		} else {
			nvt_irq_enable(false);
			NVT_LOG("request irq %d succeed\\n", client->irq);
		}'''
if anchor not in s:
    sys.exit('irq request success block not found')
sched = anchor + '''

	INIT_DELAYED_WORK(&ts->nvt_hb_work, nvt_hb_work_func);
	queue_delayed_work(ts->event_wq ? ts->event_wq : system_wq,
			   &ts->nvt_hb_work, msecs_to_jiffies(500));
	NVT_LOG("heartbeat started (500ms)\\n");'''
s = s.replace(anchor, sched, 1)

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('source: heartbeat added and scheduled')

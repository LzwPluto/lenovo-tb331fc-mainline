#!/usr/bin/env python3
"""nvt_vendor_fe_ack.py

Two things, both aligned with the vendor driver instead of periodic flashing:

1. Remove the 2 s / 8 s self-heal (it re-flashed firmware on a timer - wrong, and
   the user is right that storage wear matters).

2. Implement the vendor's special-packet handling.  Disassembly of
   nvt36523_spi.ko, nvt_ts_work_func:

       3824: cmp  w8, #0xfe          ; buf[1] == 0xFE ?
       3828: b.ne 3890
       3830: mov  w1, #0xaa         ; nvt_write_addr(SWRST_N8, 0xAA)
       3838: bl   nvt_write_addr
       3840: bl   msleep(15)        ; msleep(15)
       ...
       38b8: bl   nvt_update_firmware

   i.e. on a packet whose *first* payload byte is 0xFE the vendor resets the
   controller into idle and reloads the firmware once.  Our driver only reacts
   when bytes 1..3 are ALL 0xFD/0xFE, so a lone 0xFE packet is silently dropped
   and the controller is left waiting - which matches "touch dies after a pen
   session".

3. Also log the first bytes of any packet that fails validation (rate limited)
   so we can actually see what the controller sends.
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

# ---- 1) drop the timed self-heal, keep a plain INT-level watcher ----
start = s.find('static void nvt_hb_work_func(struct work_struct *work)')
if start < 0:
    sys.exit('watchdog not found')
end = s.find('\n}\n', start)
new = '''static void nvt_hb_work_func(struct work_struct *work)
{
	struct nvt_ts_data *ts_hb =
		container_of(work, struct nvt_ts_data, nvt_hb_work.work);
	static int last_lvl = -1;
	int lvl;

	if (!ts_hb || !ts_hb->client) {
		queue_delayed_work(ts_hb->event_wq ? ts_hb->event_wq : system_wq,
				   &ts_hb->nvt_hb_work, msecs_to_jiffies(100));
		return;
	}

	/* 只监视 INT 电平，不做任何恢复动作（避免无谓地重刷固件） */
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
print('timed self-heal removed (INT-level watcher kept)')

# ---- 2) vendor-accurate 0xFE handling ----
anchor = '''#if NVT_TOUCH_WDT_RECOVERY
	/* Controller WDT reset recovery (0xFD / 0xFE) */'''
if anchor not in s:
    sys.exit('wdt anchor not found')

fe = '''	/*
	 * Vendor behaviour (from nvt36523_spi.ko disassembly): a packet whose
	 * first payload byte is 0xFE means the controller wants to be reset into
	 * idle and reloaded.  React to a lone 0xFE, not only to the 3-byte 0xFD
	 * pattern, otherwise the controller waits forever and stops scanning.
	 */
	if (point_data[1] == 0xFE) {
		NVT_ERR("got 0xFE packet -> vendor-style reset+reload\\n");
		nvt_sw_reset_idle();
		msleep(15);
		nvt_update_firmware(ts->fw_name);
		nvt_check_fw_reset_state(RESET_STATE_REK);
		nvt_restore_cmd_func();
		goto XFER_ERROR;
	}

''' + anchor
s = s.replace(anchor, fe, 1)
print('vendor 0xFE reset+reload handling added')

# ---- 3) log rejected packets (rate limited) ----
ck = '''	if (((uint8_t)(-csum)) != point_data[65]) {'''
if ck in s:
    s = s.replace(ck, '''	if (((uint8_t)(-csum)) != point_data[65]) {
		{
			static unsigned long last_dump;
			if (time_after(jiffies, last_dump + msecs_to_jiffies(1000))) {
				last_dump = jiffies;
				NVT_LOG("pkt rejected, raw: %*ph\\n",
					10, point_data + 1);
			}
		}''', 1)
    print('rejected-packet dump added')

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('done')

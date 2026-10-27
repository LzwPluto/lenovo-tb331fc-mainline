#!/usr/bin/env python3
"""quiet_bus_during_fw_download.py

Goal: the firmware download must not disturb the display (not "repair it after").

Two differences vs Android's successful 169 ms download:
  * Android: 169 ms.  Ours: 351 ms -> we occupy the SPI/总线 and the controller
    for twice as long.
  * Android's driver stops touch scanning/interrupts while reflashing; ours keeps
    servicing touches, so reads interleave with the firmware writes.

Changes:
  1. disable the touch IRQ for the whole download (no interleaved traffic);
  2. drop the 200 us per-chunk delay I added (it was not the fix);
  3. 8 KiB chunks instead of 4 KiB (4 KiB worked, 63 KiB was truncated).
"""
import os
import sys

BASE = os.path.expanduser('~/kbuild/linux-next-tb128fu-hx83102-panel-port')
FW = os.path.join(BASE, 'drivers/input/touchscreen/nt36523_fw_update.c')
HDR = os.path.join(BASE, 'drivers/input/touchscreen/nt36523.h')
TS = os.path.join(BASE, 'drivers/input/touchscreen/nt36523_ts.c')

# ---- 1. transfer length 4 KiB -> 8 KiB ----
h = open(HDR, encoding='utf-8').read()
if '(8*1024)' in h:
    print('transfer length already 8 KiB')
else:
    h = h.replace('#define NVT_TRANSFER_LEN\t(4*1024)',
                  '#define NVT_TRANSFER_LEN\t(8*1024)', 1)
    open(HDR, 'w', encoding='utf-8', newline='\n').write(h)
    print('NVT_TRANSFER_LEN -> 8 KiB')

f = open(FW, encoding='utf-8').read()

# ---- 2. drop the settle delay ----
if '\t\tudelay(200);\n' in f:
    f = f.replace("""
		/* let the controller settle between chunks */
		udelay(200);
""", '', 1)
    print('removed per-chunk delay')

# ---- 3. extern for the irq helper ----
if 'extern void nvt_irq_enable(bool enable);' not in f:
    anchor = 'extern void Boot_Update_Firmware(struct work_struct *work);'
    if anchor in f:
        f = f.replace(anchor,
                      anchor + '\nextern void nvt_irq_enable(bool enable);', 1)
        print('declared nvt_irq_enable')

# ---- 4. quiet the bus during the boot download ----
OLD_BOOT = """	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_get_fw_info();
	nvt_set_page(ts->mmap->EVENT_BUF_ADDR);
	mutex_unlock(&ts->lock);

	/* TB331FC: Send restore commands (0xBA, 0x7F, 0x79, 0x7B) to kick controller into active scanning mode */
	nvt_restore_cmd_func();"""
NEW_BOOT = """	/*
	 * No touch traffic while reflashing: reads interleaved with the firmware
	 * writes are one of the differences to Android's clean 169 ms download.
	 */
	nvt_irq_enable(false);

	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_get_fw_info();
	nvt_set_page(ts->mmap->EVENT_BUF_ADDR);
	mutex_unlock(&ts->lock);

	/* TB331FC: Send restore commands (0xBA, 0x7F, 0x79, 0x7B) to kick controller into active scanning mode */
	nvt_restore_cmd_func();"""
if OLD_BOOT in f:
    f = f.replace(OLD_BOOT, NEW_BOOT, 1)
    print('boot work: IRQ disabled during download')
else:
    print('boot work: already patched or pattern changed')
open(FW, 'w', encoding='utf-8', newline='\n').write(f)

# ---- 5. re-enable IRQ after the drain, and quiet the hook too ----
t = open(TS, encoding='utf-8').read()

if 'static void nvt_irq_enable(bool enable)' in t:
    t = t.replace('static void nvt_irq_enable(bool enable)',
                  'void nvt_irq_enable(bool enable)', 1)
    print('nvt_irq_enable exported (non-static)')

# hook: disable IRQ around the reload
OLD_HOOK = """	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_check_fw_reset_state(RESET_STATE_REK);
	mutex_unlock(&ts->lock);

	nvt_restore_cmd_func();"""
NEW_HOOK = """	nvt_irq_enable(false);

	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_check_fw_reset_state(RESET_STATE_REK);
	mutex_unlock(&ts->lock);

	nvt_restore_cmd_func();

	nvt_irq_enable(true);"""
if OLD_HOOK in t:
    t = t.replace(OLD_HOOK, NEW_HOOK, 1)
    print('panel hook: IRQ disabled during download')
else:
    print('panel hook: already patched or pattern changed')

open(TS, 'w', encoding='utf-8', newline='\n').write(t)

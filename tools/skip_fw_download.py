#!/usr/bin/env python3
"""skip_fw_download_keep_rearm.py

Android's driver reports "Update firmware success! <169032 us>" with a valid
fw_ver/PID (0x6072); our port *always* fails it (DLM CRC mismatch, PID garbage,
or 0x0000 on the classic path).  So our firmware write is wrong -- and yet touch
used to work after Boot_Update_Firmware(), which also does:

    nvt_get_fw_info()
    nvt_set_page(ts->mmap->EVENT_BUF_ADDR)
    nvt_restore_cmd_func()          (0xBA / 0x7F / 0x79 / 0x7B)
    nvt_ts_work_func()              (drain once)

Hypothesis: the *download* is unnecessary (and its bulk SPI write to the wrong
SRAM addresses is what corrupts the display); the re-arm sequence is what
actually makes touch work.

So: skip nvt_update_firmware() everywhere and keep only the re-arm sequence, both
in the boot work and in the panel-on hook.
"""
import os
import sys

BASE = os.path.expanduser('~/kbuild/linux-next-tb128fu-hx83102-panel-port')
FW = os.path.join(BASE, 'drivers/input/touchscreen/nt36523_fw_update.c')
TS = os.path.join(BASE, 'drivers/input/touchscreen/nt36523_ts.c')

# ---------- boot work: no download, just re-arm ----------
f = open(FW, encoding='utf-8').read()

OLD_BOOT = """	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_get_fw_info();
	nvt_set_page(ts->mmap->EVENT_BUF_ADDR);
	mutex_unlock(&ts->lock);"""
NEW_BOOT = """	mutex_lock(&ts->lock);
	/*
	 * No firmware reload: our image does not match this chip's map (DLM CRC
	 * mismatch / PID reads 0x0000), and the bulk SPI write lands in SRAM the
	 * display engine uses -> content-dependent stripes.  The controller keeps
	 * its firmware; the re-arm sequence below is what actually makes touch
	 * work.
	 */
	nvt_get_fw_info();
	nvt_set_page(ts->mmap->EVENT_BUF_ADDR);
	mutex_unlock(&ts->lock);"""

if OLD_BOOT in f:
    f = f.replace(OLD_BOOT, NEW_BOOT, 1)
    open(FW, 'w', encoding='utf-8', newline='\n').write(f)
    print('boot work: firmware download skipped')
else:
    print('boot work: already patched or pattern changed')

# ---------- panel-on hook: same re-arm sequence ----------
t = open(TS, encoding='utf-8').read()

OLD_HOOK = """	mutex_lock(&ts->lock);
	nvt_restore_cmd_func();
	mutex_unlock(&ts->lock);"""
NEW_HOOK = """	mutex_lock(&ts->lock);
	nvt_get_fw_info();
	nvt_set_page(ts->mmap->EVENT_BUF_ADDR);
	mutex_unlock(&ts->lock);

	nvt_restore_cmd_func();
	nvt_ts_work_func(ts->client->irq, ts);"""

if OLD_HOOK in t:
    t = t.replace(OLD_HOOK, NEW_HOOK, 1)
    open(TS, 'w', encoding='utf-8', newline='\n').write(t)
    print('panel-on hook: re-arm only (no download)')
else:
    print('panel-on hook: already patched or pattern changed')

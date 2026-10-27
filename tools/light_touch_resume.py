#!/usr/bin/env python3
"""light_touch_resume.py

The panel's enable() hook runs a full touch firmware reload
(nvt_update_firmware + nvt_check_fw_reset_state) ~130 ms after the panel is
already scanning.  That bulk SPI write to the TDDI disturbs the display engine
and produces content-dependent stripes.

Try the lightweight variant: just ask the chip to resume/re-scan, without
pushing 196 KB of firmware at it while the display is live.
"""
import os
import shutil
import sys

P = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c')
BAK = P + '.resumebak'

s = open(P, encoding='utf-8').read()

if 'light touch resume' in s:
    print('already patched')
    sys.exit(0)

OLD = """	NVT_LOG("panel on -> re-init touch\\n");
	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_check_fw_reset_state(RESET_STATE_REK);
	mutex_unlock(&ts->lock);
	nvt_restore_cmd_func();"""

NEW = """	/* light touch resume: the full firmware reload below is a bulk SPI
	 * write to this TDDI and disturbs the display engine while the panel is
	 * already scanning (content-dependent stripes), so only ask the chip to
	 * resume scanning.  Re-enable the reload only if the chip really lost
	 * its firmware.
	 */
	NVT_LOG("panel on -> light touch resume\\n");
	mutex_lock(&ts->lock);
	nvt_check_fw_reset_state(RESET_STATE_REK);
	mutex_unlock(&ts->lock);
	nvt_restore_cmd_func();"""

if OLD not in s:
    sys.exit('panel_on_work body not found')

shutil.copy(P, BAK)
s = s.replace(OLD, NEW, 1)
open(P, 'w', encoding='utf-8', newline='\n').write(s)
print(f'patched: firmware reload removed from panel-on hook (backup {BAK})')

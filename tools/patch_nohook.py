#!/usr/bin/env python3
"""patch_nohook.py - disable the panel->touch re-init hook for a test build.

The hook runs nvt_update_firmware() + nvt_check_fw_reset_state() (a full
firmware re-download and chip reset) immediately after hx83102_enable() has
finished sending the DSI init sequence.  On this TDDI the touch and display
share one die, so resetting the touch side corrupts the display state -- which
is exactly the "stripes wherever there is content" symptom.

This patch only comments out the two call sites so we can check whether touch
still works without the hook at all.
"""
import os
import shutil
import sys

P = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c')
BAK = P + '.hookbak'

s = open(P, encoding='utf-8').read()

if 'TDDI hook disabled' in s:
    print('already patched')
    sys.exit(0)

shutil.copy(P, BAK)

OLD1 = """	if (nvt_ts_panel_event)
		nvt_ts_panel_event(true);"""
NEW1 = """	/* TDDI hook disabled: nvt_update_firmware() here resets the shared
	 * touch/display die right after DSI init and corrupts the display.
	 */
	if (0 && nvt_ts_panel_event)
		nvt_ts_panel_event(true);"""

OLD2 = """	if (nvt_ts_panel_event)
		nvt_ts_panel_event(false);"""
NEW2 = """	if (0 && nvt_ts_panel_event)
		nvt_ts_panel_event(false);"""

n = 0
if OLD1 in s:
    s = s.replace(OLD1, NEW1, 1); n += 1
if OLD2 in s:
    s = s.replace(OLD2, NEW2, 1); n += 1
if n == 0:
    sys.exit('hook call sites not found')

open(P, 'w', encoding='utf-8', newline='\n').write(s)
print(f'disabled {n} hook call site(s); backup at {BAK}')

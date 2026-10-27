#!/usr/bin/env python3
"""defer_panel_and_minimal_touch_restore.py

Two fixes:

1. Replace the blocking wait in hx83102_probe() with -EPROBE_DEFER.  Blocking
   there delayed the *touch* driver's own probe (panel probe at 4 s, touch probe
   only ran at 28.9 s), so the wait always timed out and the firmware download
   then happened at 33.9 s -- with the display already up -> stripes.

2. After a modeset the panel DSI init knocks out the touch side of the TDDI.
   Re-sending the firmware is what corrupts the display, but the chip keeps its
   firmware (rails stay powered), so only the 4 restore commands (0xBA/0x7F/
   0x79/0x7B) are needed to put it back into scanning mode.  Make the panel-on
   hook do exactly that.
"""
import os
import sys

BASE = os.path.expanduser('~/kbuild/linux-next-tb128fu-hx83102-panel-port')
PN = os.path.join(BASE, 'drivers/gpu/drm/panel/panel-himax-hx83102.c')
TS = os.path.join(BASE, 'drivers/input/touchscreen/nt36523_ts.c')

# ---------------- panel: -EPROBE_DEFER instead of blocking ----------------
p = open(PN, encoding='utf-8').read()

OLD = """	if (&nvt_fw_ready != NULL) {
		int i;

		for (i = 0; i < 400 && !nvt_fw_ready; i++)
			msleep(50);
		dev_info(&dsi->dev, "touch fw ready=%d after %d ms\\n",
			 nvt_fw_ready, i * 50);
	}
"""
NEW = """	if (&nvt_fw_ready != NULL && !nvt_fw_ready) {
		static int defer_count;

		/* -EPROBE_DEFER instead of msleep(): blocking here also delayed the
		 * touch driver's probe (it sits later in the probe chain), so the
		 * wait could never succeed and the firmware download ended up
		 * happening with the display already up.
		 */
		if (defer_count++ < 100)
			return -EPROBE_DEFER;
		dev_warn(&dsi->dev, "touch fw never became ready, proceeding\\n");
	}
"""
if OLD not in p:
    sys.exit('blocking wait block not found')
p = p.replace(OLD, NEW, 1)

# ---------------- panel: call the (now minimal) hook after enable ----------
OLD_EN = """	/*
	 * No touch re-init here.  The Novatek TDDI firmware download is a bulk
	 * SPI write to the same die and corrupts the display while the panel is
	 * scanning, so it is ordered *before* the panel is brought up instead
	 * (see the wait in hx83102_probe()).
	 */

	return 0;
}"""
NEW_EN = """	/*
	 * The panel DSI init sequence knocks the touch side of this TDDI out of
	 * scanning mode.  The hook below only re-sends the 4 restore commands --
	 * no firmware reload, because that bulk SPI write is what corrupts the
	 * display while the panel is scanning.
	 */
	if (nvt_ts_panel_event)
		nvt_ts_panel_event(true);

	return 0;
}"""
if OLD_EN not in p:
    sys.exit('enable() tail not recognised')
p = p.replace(OLD_EN, NEW_EN, 1)
open(PN, 'w', encoding='utf-8', newline='\n').write(p)
print('panel: EPROBE_DEFER + minimal touch restore in enable()')

# ---------------- touch: hook does only the restore commands ---------------
t = open(TS, encoding='utf-8').read()

OLD_WORK = """	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_check_fw_reset_state(RESET_STATE_REK);
	mutex_unlock(&ts->lock);
	nvt_restore_cmd_func();"""
NEW_WORK = """	/*
	 * Only re-arm scanning.  Do NOT reload the firmware here: the panel DSI
	 * init sequence runs just before this, and a bulk SPI write to the same
	 * die corrupts the display (content-dependent stripes).  The rails stay
	 * powered across modesets, so the firmware is still there.
	 */
	mutex_lock(&ts->lock);
	nvt_restore_cmd_func();
	mutex_unlock(&ts->lock);"""

if OLD_WORK in t:
    t = t.replace(OLD_WORK, NEW_WORK, 1)
    open(TS, 'w', encoding='utf-8', newline='\n').write(t)
    print('touch: panel-on hook now only sends restore commands')
else:
    print('touch: hook body already minimal')

#!/usr/bin/env python3
"""drop_defer_keep_restore.py

Remove the -EPROBE_DEFER experiment from hx83102_probe() (it made both the panel
and the touch driver stop probing) and keep the minimal panel-on hook: after each
modeset only the 4 restore commands are sent, never the firmware reload.

Rationale, from measurements on the device:
  * only the *firmware download* (bulk SPI write) corrupts the display;
  * the 4 restore commands are tiny and bring the touch controller back after
    the panel DSI init knocked it out.

So the sequence becomes: boot does one firmware download (~13 s, brief stripes),
then niri's first modeset re-initialises the panel (clearing the stripes) and the
minimal restore keeps touch alive.
"""
import os
import sys

PN = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c')

p = open(PN, encoding='utf-8').read()

DEFER = """	/*
	 * TB331FC: the Novatek TDDI downloads its firmware over SPI shortly after
	 * it probes.  That bulk write corrupts the display engine if the panel is
	 * already scanning, so wait here until it has finished before registering
	 * (and thereby enabling) the panel.  nvt_fw_ready is a weak symbol: if the
	 * touch driver is not built in, the display must still come up.
	 */
	if (&nvt_fw_ready != NULL && !nvt_fw_ready) {
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

if DEFER in p:
    p = p.replace(DEFER, '', 1)
    open(PN, 'w', encoding='utf-8', newline='\n').write(p)
    print('removed the EPROBE_DEFER block from hx83102_probe()')
elif 'defer_count' in p:
    sys.exit('defer block present but not recognised')
else:
    print('no defer block present')

# sanity: the minimal hook must still be called from enable()
p = open(PN, encoding='utf-8').read()
if 'nvt_ts_panel_event(true)' in p:
    print('minimal touch restore still called from enable(): yes')
else:
    print('WARNING: touch hook is NOT called from enable()')

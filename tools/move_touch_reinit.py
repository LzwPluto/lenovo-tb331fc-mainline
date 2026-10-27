#!/usr/bin/env python3
"""move_touch_reinit_before_dsi.py

Sequence today:
    unprepare(): cuts enable_gpio + regulators (1V8 pp1800 shared with touch)
        -> the Novatek TDDI loses its firmware every time the panel is unprepared
    prepare():   power up -> reset pulse -> DSI init -> 0x11 -> 0x29
    enable():    sleep 130ms -> backlight -> hook: full touch firmware reload
        -> the bulk SPI write happens while the panel is already scanning
           => content-dependent stripes

Better: run the touch re-init inside prepare(), after the reset pulse but
*before* the DSI init commands.  The display is still inactive there, so the
firmware download cannot disturb it, and by the time 0x11/0x29 are sent the
touch controller is already running.

Also make the hook synchronous: prepare() must not race with the DSI init.
"""
import os
import shutil
import sys

TS = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c')
PN = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c')

# ---- 1. touch driver: restore the full reload, make the hook synchronous ----
bak = TS + '.resumebak'
if os.path.exists(bak):
    shutil.copy(bak, TS)
    print('restored nt36523_ts.c from .resumebak (full firmware reload back)')

s = open(TS, encoding='utf-8').read()

OLD_EVENT = """void nvt_ts_panel_event(bool on)
{
	if (!ts)
		return;

	if (on)
		schedule_work(&nvt_panel_work);
}"""
NEW_EVENT = """/* Called from the panel driver's prepare(), before the DSI init commands are
 * sent, so the bulk firmware download happens while the display is inactive.
 * Must be synchronous: prepare() has to finish the re-init before it starts
 * talking DSI, otherwise the two race and the display comes up garbled.
 */
void nvt_ts_panel_event(bool on)
{
	if (!ts || !on)
		return;

	cancel_work_sync(&nvt_panel_work);
	nvt_panel_on_work(NULL);
}"""

if OLD_EVENT in s:
    s = s.replace(OLD_EVENT, NEW_EVENT, 1)
    print('touch hook is now synchronous')
elif 'nvt_panel_on_work(NULL)' not in s:
    sys.exit('nvt_ts_panel_event body not recognised')

open(TS, 'w', encoding='utf-8', newline='\n').write(s)

# ---- 2. panel driver: move the call from enable() into prepare() ----
p = open(PN, encoding='utf-8').read()

ENABLE_CALL = """	/* panel is up: let the touch controller start scanning */
	if (nvt_ts_panel_event)
		nvt_ts_panel_event(true);
"""
if ENABLE_CALL in p:
    p = p.replace(ENABLE_CALL,
                  '	/* touch re-init happens in prepare(), before DSI init */\n', 1)
    print('removed hook from hx83102_enable()')

ANCHOR = '	dsi_ctx.accum_err = ctx->desc->init(ctx);'
INSERT = """	/* The touch controller shares the panel's 1V8 rail and loses its firmware
	 * whenever the panel is unprepared.  Re-initialise it here: after the reset
	 * pulse, before the DSI init commands, i.e. while the display is still off.
	 */
	if (nvt_ts_panel_event)
		nvt_ts_panel_event(true);

"""
if INSERT not in p:
    if ANCHOR not in p:
        sys.exit('init anchor not found in prepare()')
    p = p.replace(ANCHOR, INSERT + ANCHOR, 1)
    print('inserted synchronous touch re-init into hx83102_prepare()')

open(PN, 'w', encoding='utf-8', newline='\n').write(p)
print('done')

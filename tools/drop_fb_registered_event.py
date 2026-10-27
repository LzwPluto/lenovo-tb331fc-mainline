#!/usr/bin/env python3
"""drop_fb_registered_event.py

FB_EVENT_FB_REGISTERED does not exist in this kernel's <linux/fb.h>; keep only
FB_EVENT_MODE_CHANGE and FB_EVENT_BLANK which are enough to catch the display
coming up.
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

if 'FB_EVENT_FB_REGISTERED' not in s:
    print('already clean')
    sys.exit(0)

old = '''	if (event != FB_EVENT_BLANK && event != FB_EVENT_MODE_CHANGE &&
	    event != FB_EVENT_FB_REGISTERED)
		return 0;'''
new = '''	if (event != FB_EVENT_BLANK && event != FB_EVENT_MODE_CHANGE)
		return 0;'''

if old in s:
    s = s.replace(old, new, 1)
else:
    # fall back to line-based removal
    s = '\n'.join(l for l in s.split('\n') if 'FB_EVENT_FB_REGISTERED' not in l)

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('FB_EVENT_FB_REGISTERED removed')
print('remaining FB events:')
for ln in s.split('\n'):
    if 'FB_EVENT' in ln:
        print('   ' + ln.strip())

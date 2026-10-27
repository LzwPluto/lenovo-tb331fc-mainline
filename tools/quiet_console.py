#!/usr/bin/env python3
"""quiet_console.py

The "stripes" are fbcon fighting Niri for the framebuffer: the kernel command
line contains console=tty0, so every printk is drawn straight onto the panel,
and the touch driver currently logs one line per touch frame:

    nvt_ts_work_func: touch_irq: p1=0x0A p66=0xFF cnt=1      (100+ per second)

That matches the user's description exactly - "kernel log with stripes mixed in".

Fix:
  * keep the USB serial console (ttyGS0) but drop console=tty0, so printk no
    longer paints the framebuffer
  * demote the per-frame touch log so it only prints when the finger count
    changes (keeps it useful, stops the flood)
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

old = ('\tinput_sync(ts->input_dev);\n'
       '\tNVT_LOG("touch_irq: p1=0x%02X p66=0x%02X cnt=%d\\n", point_data[1], point_data[66], finger_cnt);')
new = ('\tinput_sync(ts->input_dev);\n'
       '\t/* 只在手指数变化时记录，避免每帧刷屏（fbcon 会把日志画到屏幕上） */\n'
       '\t{\n'
       '\t\tstatic int last_cnt = -1;\n'
       '\t\tif (finger_cnt != last_cnt) {\n'
       '\t\t\tlast_cnt = finger_cnt;\n'
       '\t\t\tNVT_LOG("touch: p1=0x%02X cnt=%d\\n", point_data[1], finger_cnt);\n'
       '\t\t}\n'
       '\t}')

if old not in s:
    # try with different whitespace
    m = re.search(r'\tNVT_LOG\("touch_irq: p1=0x%02X p66=0x%02X cnt=%d\\\\n".*?\);', s)
    if not m:
        sys.exit('touch_irq log line not found')
    s = s[:m.start()] + ('{\n\t\tstatic int last_cnt = -1;\n'
                         '\t\tif (finger_cnt != last_cnt) {\n'
                         '\t\t\tlast_cnt = finger_cnt;\n'
                         '\t\t\tNVT_LOG("touch: p1=0x%02X cnt=%d\\n", point_data[1], finger_cnt);\n'
                         '\t\t}\n\t}') + s[m.end():]
    print('touch log demoted (regex path)')
else:
    s = s.replace(old, new, 1)
    print('touch log demoted')

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)

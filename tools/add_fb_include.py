#!/usr/bin/env python3
"""add_fb_include.py - the fb notifier needs <linux/fb.h>"""
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

if '#include <linux/fb.h>' in s:
    print('fb.h already included')
    sys.exit(0)

for cand in ('#include <linux/spi/spi.h>', '#include <linux/module.h>',
             '#include <linux/kernel.h>', '#include <linux/input.h>'):
    if cand in s:
        s = s.replace(cand, cand + '\n#include <linux/fb.h>', 1)
        open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
        print(f'added <linux/fb.h> after {cand}')
        sys.exit(0)

sys.exit('no include anchor found')

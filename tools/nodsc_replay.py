#!/usr/bin/env python3
"""nodsc_replay.py - replay the vendor p255_inx init sequence but skip the
Himax MIPI/DSC configuration registers (0x90/0x91/0x92), so the panel stays in
uncompressed mode. The host side also stops enabling DSC.

Rationale (measured):
  vendor init + DSC off  -> only ~half the frame updates   (panel expects compressed data)
  vendor init + DSC on   -> garbled, DSC params don't line up
  BOE init + DSC off     -> full frame, but wrong colours  (different panel)
=> keep our panel's own register sequence, just leave out its DSC setup.
"""
import os
import re
import sys

P = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c')
s = open(P, encoding='utf-8').read()

if 'p255_inx_skip_dsc' in s:
    print('already patched')
    sys.exit(0)

# 1) add a skip list inside the replay loop
old = '''		switch (dtype) {
		case 0x39:
			ret = mipi_dsi_generic_write(dsi, p, len);
			break;'''
new = '''		/*
		 * p255_inx_skip_dsc: 0x90/0x91/0x92 是 Himax 的 MIPI/DSC 配置区，
		 * 跳过它们让面板保持非压缩模式（配合 host 关闭 DSC）。
		 */
		if (len >= 1 && (p[0] == 0x90 || p[0] == 0x91 || p[0] == 0x92)) {
			i += 7 + len;
			continue;
		}

		switch (dtype) {
		case 0x39:
			ret = mipi_dsi_generic_write(dsi, p, len);
			break;'''
if old not in s:
    sys.exit('replay switch anchor not found')
s = s.replace(old, new, 1)

# 2) put our own init back, without DSC
s = s.replace('''	.has_dcs_backlight = true,
	.has_dsc = false,
	.init = boe_hx83102p_2k_init,''',
              '''	.has_dcs_backlight = true,
	.has_dsc = false,
	.init = lenovo_p255_inx_init,''')
if 'lenovo_p255_inx_init,' not in s:
    sys.exit('failed to restore lenovo_p255_inx_init')

open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('patched: skip 0x90/0x91/0x92 in replay, DSC off, vendor init restored')

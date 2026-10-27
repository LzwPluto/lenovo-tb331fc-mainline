#!/usr/bin/env python3
"""revert_slice_per_pkt.py - undo the slice_per_pkt=2 experiment."""
import os
import sys

P = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/msm/dsi/dsi_host.c')
s = open(P, encoding='utf-8').read()

n = 0
a = '''/* p255_inx slice-per-pkt = 2 (vendor DT) */
	bytes_per_pkt = dsc->slice_chunk_size * 2;'''
if a in s:
    s = s.replace(a, 'bytes_per_pkt = dsc->slice_chunk_size;', 1)
    n += 1

b = '''	/* p255_inx slice-per-pkt = 2 */
	pkt_per_line = slice_per_intf * 2;'''
if b in s:
    s = s.replace(b, '\tpkt_per_line = slice_per_intf;', 1)
    n += 1

c = 'wc = msm_host->dsc->slice_chunk_size * 2 + 1;'
if c in s:
    s = s.replace(c, 'wc = msm_host->dsc->slice_chunk_size + 1;', 1)
    n += 1

open(P, 'w', encoding='utf-8', newline='\n').write(s)
print(f'reverted {n} hunk(s); slice_per_pkt back to 1')

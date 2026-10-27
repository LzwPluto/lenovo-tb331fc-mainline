#!/usr/bin/env python3
"""add_slice_per_pkt.py - msm DSI only supports slice_per_pkt = 1, but the
p255_inx vendor DT asks for 2 (qcom,mdss-dsc-slice-per-pkt = <2>), which makes
the panel's DSC decoder reassemble slices with the wrong rhythm (partial frame).
Hard-code 2 for this port.
"""
import os
import sys

P = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/msm/dsi/dsi_host.c')
s = open(P, encoding='utf-8').read()

if 'p255_inx slice-per-pkt' in s:
    print('already patched')
    sys.exit(0)

a = 'bytes_per_pkt = dsc->slice_chunk_size; /* * slice_per_pkt; */'
if a not in s:
    sys.exit('bytes_per_pkt anchor not found')
s = s.replace(a, '''/* p255_inx slice-per-pkt = 2 (vendor DT) */
	bytes_per_pkt = dsc->slice_chunk_size * 2;''', 1)

b = '\tpkt_per_line = slice_per_intf;'
if b not in s:
    sys.exit('pkt_per_line anchor not found')
s = s.replace(b, '\t/* p255_inx slice-per-pkt = 2 */\n\tpkt_per_line = slice_per_intf * 2;', 1)

c = 'wc = msm_host->dsc->slice_chunk_size + 1;'
if c not in s:
    sys.exit('wc anchor not found')
s = s.replace(c, 'wc = msm_host->dsc->slice_chunk_size * 2 + 1;', 1)

open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('patched slice_per_pkt = 2 in msm dsi_host.c')

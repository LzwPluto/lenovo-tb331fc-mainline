#!/usr/bin/env python3
"""extract_panel.py - pull the vendor p255_inx panel node out of a stock DTS.

Prints the timing/voltage properties and the full DSI command arrays so we can
translate them into a mainline panel driver entry.
"""
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r'D:\TB331FC_GSI_Kit\device_specific_backup\tb331fc_stock.dts'
node = sys.argv[2] if len(sys.argv) > 2 else 'p255_inx'

t = open(path, encoding='utf-8', errors='replace').read()

# find the node whose name contains the wanted panel
m = re.search(r'^[ \t]*([A-Za-z0-9_,.\-]*' + re.escape(node) + r'[A-Za-z0-9_,.\-]*)[ \t]*\{', t, re.M)
if not m:
    print('node not found')
    sys.exit(1)
start = m.start()
name = m.group(1)

# brace matching
j = t.index('{', m.start())
depth = 0
k = j
while k < len(t):
    if t[k] == '{':
        depth += 1
    elif t[k] == '}':
        depth -= 1
        if depth == 0:
            break
    k += 1
body = t[j + 1:k]

print(f'=== node: {name} (line {t[:start].count(chr(10)) + 1}) ===')

# properties of interest
simple = [
    'qcom,mdss-dsi-panel-width', 'qcom,mdss-dsi-panel-height',
    'qcom,mdss-dsi-panel-framerate', 'qcom,mdss-dsi-panel-type',
    'qcom,mdss-dsi-bpp', 'qcom,mdss-dsi-underflow-color',
    'qcom,mdss-dsi-border-color', 'qcom,mdss-dsi-traffic-mode',
    'qcom,mdss-dsi-bllp-eof-power-mode', 'qcom,mdss-dsi-bllp-power-mode',
    'qcom,mdss-dsi-lane-0-state', 'qcom,mdss-dsi-lane-1-state',
    'qcom,mdss-dsi-lane-2-state', 'qcom,mdss-dsi-lane-3-state',
    'qcom,mdss-dsi-t-clk-post', 'qcom,mdss-dsi-t-clk-pre',
    'qcom,mdss-dsi-h-front-porch', 'qcom,mdss-dsi-h-back-porch',
    'qcom,mdss-dsi-h-pulse-width', 'qcom,mdss-dsi-h-sync-skew',
    'qcom,mdss-dsi-v-front-porch', 'qcom,mdss-dsi-v-back-porch',
    'qcom,mdss-dsi-v-pulse-width', 'qcom,mdss-dsi-h-sync-polarity',
    'qcom,mdss-dsi-panel-clockrate',
    'qcom,mdss-dsi-panel-phy-timings',
    'qcom,mdss-dsi-panel-orientation',
    'qcom,mdss-dsi-bl-pmic-control-type',
    'qcom,mdss-dsi-bl-min-level', 'qcom,mdss-dsi-bl-max-level',
    'qcom,mdss-dsi-bl-inverted-dbv',
    'qcom,mdss-dsi-reset-sequence',
    'qcom,mdss-dsi-panel-status-check-mode',
    'qcom,mdss-dsi-stream', 'qcom,mdss-dsi-mdp-trigger',
    'qcom,mdss-dsi-dma-trigger', 'qcom,mdss-dsi-panel-timings',
]
for p in simple:
    mm = re.search(r'^[ \t]*' + re.escape(p) + r'\s*=\s*([^;]+);', body, re.M)
    if mm:
        v = mm.group(1).strip()
        if len(v) > 120:
            v = v[:120] + ' ...'
        print(f'  {p:<42} {v}')

print()
print('=== command arrays ===')
for p in ('qcom,mdss-dsi-on-command', 'qcom,mdss-dsi-off-command',
          'qcom,mdss-dsi-post-init', 'qcom,mdss-dsi-init'):
    mm = re.search(r'^[ \t]*' + re.escape(p) + r'\s*=\s*\[([^\]]*)\];', body, re.M | re.S)
    if not mm:
        continue
    # decode
    raw = mm.group(1)
    data = []
    for tok in raw.split():
        try:
            data.append(int(tok, 16))
        except ValueError:
            pass
    print(f'\n  --- {p} : {len(data)} bytes ---')
    # DSI packets: type, count(2 bytes LE), payload...
    i = 0
    line = 0
    while i + 3 <= len(data):
        dtype = data[i]
        ln = data[i + 1] | (data[i + 2] << 8)
        payload = data[i + 3:i + 3 + ln]
        i += 3 + ln
        hexs = ' '.join(f'{b:02x}' for b in payload)
        print(f'    pkt{line:02d} type=0x{dtype:02x} len={ln:3d}: {hexs}')
        line += 1
        if line > 80:
            print('    ... (truncated)')
            break

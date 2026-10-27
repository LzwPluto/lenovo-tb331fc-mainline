#!/usr/bin/env python3
"""fix_wifi_bt_dt.py

Two DT fixes surfaced when the WCN3990 drivers finally probed:

1) Bluetooth: qcom_geni_serial bails out with "Invalid line -19" because the BT
   UART (serial@4a8c000) has no serialN alias.  Add serial1 for it so serdev can
   instantiate the qcom,wcn3990-bt child and hci_qca can probe.

2) WiFi: ath10k_snoc asks for vdd-3.3-ch1-supply but the DTB only describes
   vdd-3.3-ch0-supply, so it falls back to a dummy regulator.  Point ch1 at the
   same regulator as ch0.
"""
import re
import sys

SRC = '/mnt/d/TB331FCLinux/build/ref_nvt3.dts'
DST = '/mnt/d/TB331FCLinux/build/ref_wifibt.dts'

t = open(SRC, encoding='utf-8').read()

# --- 1) serial1 alias for the Bluetooth UART ---
if 'serial1 =' not in t:
    old = '\t\tserial0 = "/soc@0/geniqup@4ac0000/serial@4a90000";'
    if old not in t:
        sys.exit('serial0 alias anchor not found')
    t = t.replace(old, old + '\n\t\tserial1 = "/soc@0/geniqup@4ac0000/serial@4a8c000";', 1)
    print('added serial1 alias for the Bluetooth UART')
else:
    print('serial1 alias already present')

# --- 2) vdd-3.3-ch1-supply on the wifi node ---
i = t.find('wifi@c800000 {')
if i < 0:
    sys.exit('wifi node not found')
j = t.index('{', i)
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

if 'vdd-3.3-ch1-supply' in body:
    print('vdd-3.3-ch1-supply already present')
else:
    m = re.search(r'(\s*)vdd-3\.3-ch0-supply = <(0x[0-9a-f]+)>;', body)
    if not m:
        sys.exit('vdd-3.3-ch0-supply not found in wifi node')
    ch0 = m.group(2)
    body = body.replace(
        m.group(0),
        m.group(0) + f'{m.group(1)}vdd-3.3-ch1-supply = <{ch0}>;', 1)
    t = t[:j + 1] + body + t[k:]
    print(f'added vdd-3.3-ch1-supply = <{ch0}> (same rail as ch0)')

open(DST, 'w', encoding='utf-8', newline='\n').write(t)
print(f'wrote {DST}')

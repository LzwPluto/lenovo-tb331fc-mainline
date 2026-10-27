#!/usr/bin/env python3
"""fix_l16_voltage.py

pm6125_l16 feeds the WCN3990 crystal oscillator (BT "vdd-xtal", WiFi "vdd-1.8-xo").
Android's regulator_summary shows it running at exactly 1800000 uV:

    pm6125_l16   2   2   0   idle   1800mV   min 1700mV  max 1900mV
       c800000.qcom,icnss-vdd-1.8-xo   1   0mA   1800mV   1800mV

Our DTB only states the range 1700000..1900000, so the regulator framework picks
the *minimum* (1.7 V).  A 100 mV deficit on the XO rail can keep the oscillator
from starting, which would explain why both Bluetooth (UART, no response) and
WiFi (no QMI service) fail on the same chip.

Pin it to 1800000 uV (0x1b7740) like l17 was pinned to 1304000 uV.
"""
import re
import sys

P = '/mnt/d/TB331FCLinux/build/CANONICAL.dts'
t = open(P, encoding='utf-8').read()

start = t.find('regulators-0 {')
if start < 0:
    sys.exit('regulators-0 not found')
brace = t.index('{', start)
depth = 0; k = brace
while k < len(t):
    if t[k] == '{':
        depth += 1
    elif t[k] == '}':
        depth -= 1
        if depth == 0:
            break
    k += 1
block = t[brace + 1:k]

m = re.search(r'(l16 \{)(.*?)(\n\t+\};)', block, re.S)
if not m:
    sys.exit('l16 node not found')
body = m.group(2)
if '0x1b7740' in body and 'regulator-max-microvolt = <0x1b7740>' in body:
    print('l16 already pinned to 1800000')
    sys.exit(0)

orig = body
body = re.sub(r'regulator-min-microvolt = <0x[0-9a-f]+>;',
              'regulator-min-microvolt = <0x1b7740>;', body)
body = re.sub(r'regulator-max-microvolt = <0x[0-9a-f]+>;',
              'regulator-max-microvolt = <0x1b7740>;', body)
if body == orig:
    sys.exit('nothing changed')

block = block[:m.start(2)] + body + block[m.end(2):]
t = t[:brace + 1] + block + t[k:]
open(P, 'w', encoding='utf-8', newline='\n').write(t)

print('l16 pinned to 1800000 uV (0x1b7740) - matches the Android measurement')
for line in body.strip().split('\n'):
    if 'microvolt' in line or 'phandle' in line:
        print('   ' + line.strip())

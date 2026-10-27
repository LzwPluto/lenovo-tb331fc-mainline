#!/usr/bin/env python3
"""fix_bt_uart_ctsrts.py

qcom_geni_serial set the qup3 pin state with only gpio8/gpio9 (TX/RX).  If the
UART runs with hardware flow control the transmitter waits for CTS, which is not
routed, so every HCI command still times out.  Extend the qup3 pin state to the
full four-pin group (gpio8..gpio11).
"""
import re
import sys

P = '/mnt/d/TB331FCLinux/build/CANONICAL.dts'
t = open(P, encoding='utf-8').read()

if '"gpio8\\0gpio9\\0gpio10\\0gpio11"' in t:
    print('qup3 already covers 4 pins')
    sys.exit(0)

old = 'pins = "gpio8\\0gpio9";'
if old not in t:
    sys.exit('qup3 two-pin state not found')
n = t.count(old)
t = t.replace(old, 'pins = "gpio8\\0gpio9\\0gpio10\\0gpio11";')
open(P, 'w', encoding='utf-8', newline='\n').write(t)
print(f'extended {n} qup3 pin state(s) to gpio8..gpio11 (TX/RX/CTS/RTS)')

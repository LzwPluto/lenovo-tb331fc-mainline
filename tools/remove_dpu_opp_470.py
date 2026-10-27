#!/usr/bin/env python3
"""remove_dpu_opp_470.py - revert the 470 MHz OPP entry (it caused stripes)"""
import re
import sys

P = '/mnt/d/TB331FCLinux/build/CANONICAL.dts'
t = open(P, encoding='utf-8').read()

before = t
t = re.sub(r'\n\s*opp-470000000 \{\n\s*opp-hz = <0x00 0x1c03a180>;\n\s*required-opps = <0x1a>;\n\s*\};\n', '', t)
if t == before:
    print('no 470 MHz entry found (already clean)')
else:
    open(P, 'w', encoding='utf-8', newline='\n').write(t)
    print('removed the 470 MHz OPP entry - DPU back to 384 MHz only')

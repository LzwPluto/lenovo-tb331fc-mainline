#!/usr/bin/env python3
"""add_spi_dmas.py

Restore the DMA properties on spi@4a80000 using the exact values from the
vendor DTB (ref.dts):

    dmas = <0x46 0x00 0x00 0x01 0x46 0x01 0x00 0x01>;
    dma-names = "tx", "rx";

They had been removed because the GPI DMA controller was still deferring at the
time.  Now /sys/class/dma/dma0chan* exists, so SPI can use DMA instead of the
CPU-driven PIO path, which should stop the touch driver's transfers from
stealing AHB/interconnect bandwidth away from the DPU (content-dependent
stripes that vanish as soon as the touch driver is unbound).
"""
import os
import sys

SRC = '/mnt/d/TB331FCLinux/build/CANONICAL_383.dts'
DST = '/mnt/d/TB331FCLinux/build/CANONICAL_383_dma.dts'

t = open(SRC, encoding='utf-8').read()

# locate the spi@4a80000 node body
i = t.find('spi@4a80000 {')
if i < 0:
    sys.exit('spi@4a80000 not found')
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

if 'dmas =' in body:
    print('dmas already present')
    open(DST, 'w', encoding='utf-8', newline='\n').write(t)
    sys.exit(0)

anchor = '\t\t\t\tinterrupts = <0x00 0x147 0x04>;\n'
if anchor not in body:
    sys.exit('interrupts anchor not found in spi node')

ins = ('\t\t\t\tdmas = <0x46 0x00 0x00 0x01 0x46 0x01 0x00 0x01>;\n'
       '\t\t\t\tdma-names = "tx\\0rx";\n')
body = body.replace(anchor, anchor + ins, 1)

t = t[:j + 1] + body + t[k:]
open(DST, 'w', encoding='utf-8', newline='\n').write(t)

# report
print('inserted:')
print('  dmas = <0x46 0x00 0x00 0x01 0x46 0x01 0x00 0x01>;')
print('  dma-names = "tx", "rx";')
print(f'wrote {DST}')

#!/usr/bin/env python3
"""disable_spi_dma.py

The touch controller shares the GENI SPI controller at 4a80000.  Its firmware
download is a ~192 KB burst that currently runs through DMA.  The stripes that
appear in fbcon / Niri at exactly those moments suggest the SPI DMA is writing
outside its intended buffers (broken descriptor or IOMMU mapping), scribbling
over framebuffer memory.

Removing dmas/dma-names from the SPI node forces the SPI core into PIO mode,
which is much slower but cannot touch unrelated memory.  If the stripes vanish,
the DMA path is confirmed as the culprit.
"""
import re
import sys

P = '/mnt/d/TB331FCLinux/build/CANONICAL.dts'
t = open(P, encoding='utf-8').read()

i = t.find('spi@4a80000 {')
if i < 0:
    sys.exit('spi@4a80000 not found')
brace = t.index('{', i)
depth = 0; k = brace
while k < len(t):
    if t[k] == '{':
        depth += 1
    elif t[k] == '}':
        depth -= 1
        if depth == 0:
            break
    k += 1
body = t[brace + 1:k]

if 'dmas =' not in body:
    print('no dmas in the SPI node - nothing to do')
    sys.exit(0)

before = body
body = re.sub(r'\n\t+dmas = <[^;]+>;', '', body)
body = re.sub(r'\n\t+dma-names = "[^"]*";', '', body)
if body == before:
    sys.exit('dmas found but not removed (pattern mismatch)')

t = t[:brace + 1] + body + t[k:]
open(P, 'w', encoding='utf-8', newline='\n').write(t)

print('removed dmas/dma-names from spi@4a80000 -> PIO mode')
print('remaining SPI node properties:')
for line in body.strip().split('\n'):
    s = line.strip()
    if s and not s.startswith('}') and 'touchscreen@' not in s:
        print('   ' + s)

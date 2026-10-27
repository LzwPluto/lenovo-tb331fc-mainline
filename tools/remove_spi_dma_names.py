#!/usr/bin/env python3
"""remove_spi_dma_names.py - drop the leftover dma-names from spi@4a80000"""
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

before = body
body = re.sub(r'\n\t+dma-names = [^;]+;', '', body)
body = re.sub(r'\n\t+dmas = [^;]+;', '', body)
if body == before:
    print('nothing left to remove')
else:
    t = t[:brace + 1] + body + t[k:]
    open(P, 'w', encoding='utf-8', newline='\n').write(t)
    print('removed remaining DMA properties from spi@4a80000')

print('SPI node now:')
for line in body.strip().split('\n'):
    s = line.strip()
    if s.startswith(('dma', 'compatible = "qcom,geni-spi"', 'spi-max-frequency', 'status = "okay"')):
        print('   ' + s)

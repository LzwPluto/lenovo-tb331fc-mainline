#!/usr/bin/env python3
"""fix_dpu_opp_470.py

Two mistakes from the first attempt:
  * 470000000 is 0x1c03a180, not 0x1c04c600
  * the entry was inserted before the node's properties, and dtc requires all
    properties to come before child nodes (FATAL ERROR: Unable to parse input tree)

Remove the bad entry and append the correct one after the existing children.
"""
import re
import sys

P = '/mnt/d/TB331FCLinux/build/CANONICAL.dts'
t = open(P, encoding='utf-8').read()

# 1) drop whatever wrong entry is there
t = re.sub(r'\n\t+opp-470000000 \{\n\t+opp-hz = <0x00 0x[0-9a-f]+>;\n\t+\};\n', '', t)

# 2) locate the DPU opp-table again (phandle 0x72)
target = None
for m in re.finditer(r'opp-table \{', t):
    brace = t.index('{', m.start())
    depth = 0; k = brace
    while k < len(t):
        if t[k] == '{':
            depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    body = t[brace:k + 1]
    if 'phandle = <0x72>;' in body:
        target = (brace, k, body)
        break

if not target:
    sys.exit('DPU opp-table (phandle 0x72) not found')

brace, end, body = target
mm = re.search(r'\n(\t+)opp-384000000 \{', body)
if not mm:
    sys.exit('opp-384000000 child not found')
indent = mm.group(1)

entry = (f'\n{indent}opp-470000000 {{'
         f'\n{indent}\topp-hz = <0x00 0x1c03a180>;'   # 470000000
         f'\n{indent}}};')

# append at the end of the node body, just before its closing brace
t = t[:end] + entry + '\n' + t[end:].lstrip('\n')
# normalize: ensure the closing brace indentation stays sane
open(P, 'w', encoding='utf-8', newline='\n').write(t)

t2 = open(P, encoding='utf-8').read()
i = t2.find('opp-470000000')
print('inserted:')
print(t2[i - 120:i + 160])

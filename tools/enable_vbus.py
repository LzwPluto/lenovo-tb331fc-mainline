#!/usr/bin/env python3
"""Enable the vbus_p1 fixed regulator (USB-C port VBUS) so host mode can power
an attached device."""
import re, sys

src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()

m = re.search(r'\tregulator-0 \{\n', t)
if not m:
    print('!! regulator-0 node not found')
    sys.exit(1)

start = m.end()
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

if 'regulator-always-on' not in body:
    body = '\n\t\tregulator-always-on;\n\t\tregulator-boot-on;' + body
body = re.sub(r'status = "[^"]*";', 'status = "okay";', body)

t = t[:j + 1] + body + t[k:]
open(dst, 'w', encoding='utf-8', newline='\n').write(t)

# show result
i = t.find('\tregulator-0 {')
print(t[i:i + 400])

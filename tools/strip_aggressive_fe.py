#!/usr/bin/env python3
"""strip_aggressive_fe.py - remove every copy of the single-0xFE handler

The vendor only reacts to 0xFE after six 0xFD/0xFE bytes AND more than ten
consecutive occurrences; a lone 0xFE must be parsed normally.  Patch scripts were
re-run a few times and left duplicates, so strip them all here.
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

removed = 0
while True:
    i = s.find('if (point_data[1] == 0xFE) {')
    if i < 0:
        break
    # walk back over the preceding comment block
    start = i
    prev = s.rfind('\t/*', 0, i)
    if prev >= 0 and i - prev < 600:
        start = prev
    # find the closing brace of the if
    brace = s.index('{', i)
    depth = 0
    k = brace
    while k < len(s):
        if s[k] == '{':
            depth += 1
        elif s[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    end = k + 1
    while end < len(s) and s[end] in ' \t\r\n':
        end += 1
    s = s[:start] + s[end:]
    removed += 1

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print(f'removed {removed} aggressive 0xFE handler(s)')

# verify the vendor-style block survived
if 'all_err' in s and 'err_run > 10' in s:
    print('vendor-style WDT block present and intact')
else:
    print('WARNING: vendor-style WDT block missing!')

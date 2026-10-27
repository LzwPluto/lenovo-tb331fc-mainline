#!/usr/bin/env python3
"""fix_errrun_scope.py - move the error-run counter to the outer block"""
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

old = '''	{
		/* vendor: bytes 1..6 must all be 0xFD/0xFE, i.e. (b + 3) & 0xFF <= 1 */
		bool all_err = true;
		int k;
'''
new = '''	{
		/* vendor: bytes 1..6 must all be 0xFD/0xFE, i.e. (b + 3) & 0xFF <= 1 */
		static unsigned int err_run;
		bool all_err = true;
		int k;
'''
if old not in s:
    sys.exit('outer block anchor not found')
s = s.replace(old, new, 1)

# drop the inner (now duplicate) declaration
inner = '''		if (all_err) {
			static unsigned int err_run;

			err_run++;'''
inner_new = '''		if (all_err) {
			err_run++;'''
if inner in s:
    s = s.replace(inner, inner_new, 1)
    print('inner duplicate declaration removed')
else:
    print('inner declaration pattern not found (check manually)')

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('err_run moved to the outer block')

#!/usr/bin/env python3
"""force_classic_fw_path.py

Evidence chain:
  * Android downloads the touch firmware while the display is up and it does NOT
    corrupt the display -> the download itself is fine;
  * our driver takes the "cascade / auto copy" branch, where the chip DMAs the
    firmware to addresses taken from a *second header at the end of the file*;
  * our driver has always reported a DLM CRC mismatch and garbage PID, i.e. its
    interpretation of this firmware image does not match the vendor's;
  * symptom is stripes *wherever there is content*, i.e. memory the display
    engine reads got overwritten.

So force the classic (non-cascade) path: the driver writes ILM/DLM explicitly to
the addresses in nt36523_mem_map.h instead of letting the chip auto-copy to
addresses parsed from the file.
"""
import os
import sys

P = os.path.expanduser(
    '~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_fw_update.c')

s = open(P, encoding='utf-8').read()

OLD = '	cascade_2nd_header_info = (fwdata[0x20] & 0x02) >> 1;'
NEW = ('	/*\n'
       '	 * Forced to 0: the cascade path lets the chip DMA the firmware to\n'
       '	 * addresses parsed from a trailing header, and our parsing of this\n'
       '	 * image does not match the vendor driver (DLM CRC mismatch, garbage\n'
       '	 * PID).  Writing ILM/DLM explicitly to the addresses in\n'
       '	 * nt36523_mem_map.h is the conservative path.\n'
       '	 */\n'
       '	cascade_2nd_header_info = 0;')

if OLD not in s:
    sys.exit('cascade assignment not found')
s = s.replace(OLD, NEW, 1)
open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('forced classic firmware write path (cascade disabled)')

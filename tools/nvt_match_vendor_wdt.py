#!/usr/bin/env python3
"""nvt_match_vendor_wdt.py

Correct the 0xFE handling to match the vendor exactly.

Vendor logic (from nvt36523_spi.ko, nvt_ts_work_func):

    for (i = 1; i <= 6; i++)
        if (((buf[i] + 3) & 0xFF) > 1) goto normal_parse;   /* buf[i] must be 0xFD or 0xFE */
    if (++consecutive <= 10) goto normal_parse;
    if (buf[1] != 0xFE) { read_fw_history(); nvt_update_firmware(); }   /* 0xFD -> reload */
    else                { nvt_write_addr(SWRST_N8, 0xAA); msleep(15); ... }  /* 0xFE -> reset to idle */

So:
  * the trigger is SIX bytes all 0xFD/0xFE, not three
  * recovery only happens after MORE THAN 10 such packets in a row
  * a lone 0xFE packet must be parsed normally, not reset

Replace our earlier (too aggressive) single-0xFE handler with this behaviour and
keep the rejected-packet dump so we can see what the controller actually sends.
"""
import re
import sys

SRC = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(SRC, encoding='utf-8').read()

# 1) remove the single-0xFE block added earlier
start = s.find('\t/*\n\t * Vendor behaviour (from nvt36523_spi.ko disassembly)')
if start >= 0:
    end = s.find('goto XFER_ERROR;\n\t}\n\n', start)
    if end < 0:
        sys.exit('could not locate end of the 0xFE block')
    end += len('goto XFER_ERROR;\n\t}\n\n')
    s = s[:start] + s[end:]
    print('removed the too-aggressive single-0xFE handler')
else:
    print('single-0xFE handler not present (fine)')

# 2) replace the 3-byte WDT pattern with the vendor's 6-byte + counter logic
old = '''	if ((point_data[1] == 0xFD || point_data[1] == 0xFE) &&
	    (point_data[2] == 0xFD || point_data[2] == 0xFE) &&
	    (point_data[3] == 0xFD || point_data[3] == 0xFE)) {
		if (nvt_wdt_fw_recovery(point_data)) {
			NVT_ERR("Recover for fw reset, 0x%02X\\n", point_data[1]);
			nvt_update_firmware(ts->fw_name);
			nvt_restore_cmd_func();
		}
		goto XFER_ERROR;
	}'''
new = '''	{
		/* vendor: bytes 1..6 must all be 0xFD/0xFE, i.e. (b + 3) & 0xFF <= 1 */
		bool all_err = true;
		int k;

		for (k = 1; k <= 6; k++) {
			if (((point_data[k] + 3) & 0xFF) > 1) {
				all_err = false;
				break;
			}
		}

		if (all_err) {
			static unsigned int err_run;

			err_run++;
			if (err_run > 10) {
				err_run = 0;
				if (point_data[1] != 0xFE) {
					NVT_ERR("fw reload after error run (0x%02X)\\n",
						point_data[1]);
					nvt_update_firmware(ts->fw_name);
					nvt_check_fw_reset_state(RESET_STATE_REK);
					nvt_restore_cmd_func();
				} else {
					NVT_ERR("got 0xFE run -> reset to idle\\n");
					nvt_sw_reset_idle();
					msleep(15);
					nvt_restore_cmd_func();
				}
			}
			goto XFER_ERROR;
		}
		err_run = 0;
	}'''

if old in s:
    s = s.replace(old, new, 1)
    print('WDT pattern replaced with vendor 6-byte + >10 counter logic')
else:
    print('WDT block not found verbatim - leaving as is')

open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
print('done')

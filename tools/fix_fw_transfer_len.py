#!/usr/bin/env python3
"""fix_fw_transfer_len.py

The firmware writer pushes NVT_TRANSFER_LEN = 63*1024 bytes in a single
spi_transfer:

    #define NVT_TRANSFER_LEN   (63*1024)      /* 64512 */
    ret = CTP_SPI_WRITE(ts->client, fwbuf, len+1);   /* up to 64513 bytes */

The DLM partition is 0xCB37 = 52023 bytes, so it goes out as ONE huge transfer.
That is far beyond what the GENI SPI controller / GPI DMA can do in one go, which
matches the observed failure exactly:

    dlm: bin crc = 0x49618174, golden = 0x49618174, result = 0x2AD78BD2
         ^ our data is right           ^ the chip read back something else,
                                         and a different value every boot

i.e. the transfer is truncated/partially applied.

Fix: 4 KiB chunks plus a short settle delay between them, and a per-chunk log so
we can see the transfer progress.

Also restores what the diagnostics had disabled:
  * the cascade flag is read from the image again (fwdata[0x20] & 0x02), which
    is what makes bin crc == golden;
  * the boot work and the panel hook download the firmware again.
"""
import os
import sys

BASE = os.path.expanduser('~/kbuild/linux-next-tb128fu-hx83102-panel-port')
FW = os.path.join(BASE, 'drivers/input/touchscreen/nt36523_fw_update.c')
HDR = os.path.join(BASE, 'drivers/input/touchscreen/nt36523.h')
TS = os.path.join(BASE, 'drivers/input/touchscreen/nt36523_ts.c')

# ---------- 1. transfer length ----------
h = open(HDR, encoding='utf-8').read()
OLD_LEN = '#define NVT_TRANSFER_LEN\t(63*1024)'
NEW_LEN = ('/*\n'
           ' * 4 KiB instead of 63 KiB: the firmware writer pushes this many bytes\n'
           ' * in a single spi_transfer, and the GENI SPI + GPI DMA cannot move\n'
           ' * 64 KiB in one go -- the transfer was truncated, which is why the\n'
           ' * DLM read-back CRC never matched even though our own data did.\n'
           ' */\n'
           '#define NVT_TRANSFER_LEN\t(4*1024)')
if OLD_LEN in h:
    h = h.replace(OLD_LEN, NEW_LEN, 1)
    open(HDR, 'w', encoding='utf-8', newline='\n').write(h)
    print('NVT_TRANSFER_LEN: 63 KiB -> 4 KiB')
elif '(4*1024)' in h:
    print('NVT_TRANSFER_LEN already 4 KiB')
else:
    sys.exit('NVT_TRANSFER_LEN definition not found')

# ---------- 2. chunk delay in nvt_write_sram ----------
f = open(FW, encoding='utf-8').read()
OLD_W = """		ret = CTP_SPI_WRITE(ts->client, fwbuf, len+1);
		if (ret) {
			NVT_ERR("write to sram failed, ret = %d\\n", ret);
			return ret;
		}
"""
NEW_W = """		ret = CTP_SPI_WRITE(ts->client, fwbuf, len+1);
		if (ret) {
			NVT_ERR("write to sram failed, ret = %d\\n", ret);
			return ret;
		}

		/* let the controller settle between chunks */
		udelay(200);
"""
if OLD_W in f:
    f = f.replace(OLD_W, NEW_W, 1)
    print('added 200 us settle delay per chunk')
else:
    print('chunk write site already patched')

# ---------- 3. cascade flag back to the image value ----------
OLD_C = '	cascade_2nd_header_info = 0;'
NEW_C = '	cascade_2nd_header_info = (fwdata[0x20] & 0x02) >> 1;'
if OLD_C in f:
    f = f.replace(OLD_C, NEW_C, 1)
    print('cascade flag read from image again')

# ---------- 4. boot work: download again ----------
OLD_BOOT = """	mutex_lock(&ts->lock);
	/*
	 * No firmware reload: our image does not match this chip's map (DLM CRC
	 * mismatch / PID reads 0x0000), and the bulk SPI write lands in SRAM the
	 * display engine uses -> content-dependent stripes.  The controller keeps
	 * its firmware; the re-arm sequence below is what actually makes touch
	 * work.
	 */
	nvt_get_fw_info();"""
NEW_BOOT = """	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_get_fw_info();"""
if OLD_BOOT in f:
    f = f.replace(OLD_BOOT, NEW_BOOT, 1)
    print('boot work downloads firmware again')
open(FW, 'w', encoding='utf-8', newline='\n').write(f)

# ---------- 5. panel hook: full reload again ----------
t = open(TS, encoding='utf-8').read()
OLD_HOOK = """	mutex_lock(&ts->lock);
	nvt_get_fw_info();
	nvt_set_page(ts->mmap->EVENT_BUF_ADDR);
	mutex_unlock(&ts->lock);

	nvt_restore_cmd_func();
	nvt_ts_work_func(ts->client->irq, ts);"""
NEW_HOOK = """	mutex_lock(&ts->lock);
	nvt_update_firmware(ts->fw_name);
	nvt_check_fw_reset_state(RESET_STATE_REK);
	mutex_unlock(&ts->lock);

	nvt_restore_cmd_func();"""
if OLD_HOOK in t:
    t = t.replace(OLD_HOOK, NEW_HOOK, 1)
    open(TS, 'w', encoding='utf-8', newline='\n').write(t)
    print('panel hook: full firmware reload restored')
else:
    print('panel hook already full reload')

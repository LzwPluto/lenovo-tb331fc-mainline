#!/usr/bin/env python3
"""parse_nvt_fw.py

Parse the Novatek NT36523N firmware image exactly the way the driver does, so we
can see the ILM/DLM target SRAM addresses, sizes, CRCs and the cascade flag.

Driver parsing (nt36523_fw_update.c, nvt_bin_header_parser):
  entry[i] at 0x00 + i*12 : BIN_addr (u32), SRAM_addr (u32), size (u32)
  ILM/DLM crc at 0x18 / 0x1C
  cascade flag = (fwdata[0x20] & 0x02) >> 1
  additional partitions: cascade ? header at end-0x10 : at 0x30 + idx*0x10
  each: SRAM_addr(u32), size(u32), BIN_addr(u32), crc(u32)
"""
import struct
import sys

p = sys.argv[1]
d = open(p, 'rb').read()
print(f'file: {p}  size={len(d)} bytes (0x{len(d):X})')

def u32(off):
    return struct.unpack_from('<I', d, off)[0]

print('\n=== partition entries (0x00, 0x0C) ===')
for i, name in enumerate(('ILM', 'DLM')):
    off = i * 12
    bin_addr, sram_addr, size = u32(off), u32(off + 4), u32(off + 8)
    print(f'  {name}: BIN_addr=0x{bin_addr:06X}  SRAM_addr=0x{sram_addr:06X}  '
          f'size={size} (0x{size:X})  bin range 0x{bin_addr:06X}-0x{bin_addr+size:06X}')

print('\n=== crc fields ===')
print(f'  0x18 = 0x{u32(0x18):08X}   0x1C = 0x{u32(0x1C):08X}')
if u32(0x18) and u32(0x1C):
    print('   (driver: hw_crc ? 0x18/0x1C are ILM/DLM crc : computed checksums)')

print('\n=== flags ===')
b20 = d[0x20]
print(f'  fwdata[0x20] = 0x{b20:02X}   cascade_2nd_header_info = {(b20 >> 1) & 1}')

end = len(d)
print('\n=== extra partitions ===')
cascade = (b20 >> 1) & 1
for idx in range(3):
    pos = (end - 0x10) if cascade else (0x30 + 0x10 * idx)
    if pos + 16 > len(d):
        continue
    sram, size, bin_addr, crc = u32(pos), u32(pos + 4), u32(pos + 8), u32(pos + 12)
    print(f'  [{idx}] pos=0x{pos:X}: SRAM=0x{sram:06X} size={size} '
          f'BIN=0x{bin_addr:06X} crc=0x{crc:08X}')

print('\n=== second header region (last 32 bytes) ===')
for off in range(end - 32, end, 16):
    print(f'  0x{off:X}: ' + ' '.join(f'{b:02X}' for b in d[off:off + 16]))

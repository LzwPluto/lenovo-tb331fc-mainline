#!/usr/bin/env python3
"""verify_vb2.py - correct vendor_boot v4 header offsets.

v4 layout:
  0x00 magic[8]        0x08 header_version   0x0C page_size
  0x10 kernel_addr     0x14 ramdisk_addr     0x18 vendor_ramdisk_size
  0x1C cmdline[2048]
  0x81C tags_addr      0x820 name[16]
  0x830 header_size    0x834 dtb_size        0x838 dtb_addr(u64)
  0x840 vendor_ramdisk_table_size
  0x844 table_entry_num   0x848 table_entry_size   0x84C bootconfig_size
"""
import struct
import sys

p = sys.argv[1]
d = open(p, 'rb').read()
assert d[:8] == b'VNDRBOOT', 'not vendor_boot'

page = struct.unpack_from('<I', d, 0x0C)[0]
vr_size = struct.unpack_from('<I', d, 0x18)[0]
hdr_size = struct.unpack_from('<I', d, 0x830)[0]
dtb_size = struct.unpack_from('<I', d, 0x834)[0]
dtb_addr = struct.unpack_from('<Q', d, 0x838)[0]
vrt_size = struct.unpack_from('<I', d, 0x840)[0]
vrt_num = struct.unpack_from('<I', d, 0x844)[0]
bc_size = struct.unpack_from('<I', d, 0x84C)[0]

print(f'{p}')
print(f'  page={page} hdr_size={hdr_size} vr_size={vr_size}')
print(f'  dtb_size={dtb_size} dtb_addr=0x{dtb_addr:x}')
print(f'  vrt_size={vrt_size} entries={vrt_num} bootconfig={bc_size}')

off = -1
for cand in range(0, len(d) - 4, page):
    if d[cand:cand + 4] == b'\xd0\x0d\xfe\xed':
        off = cand
        break
fdt_total = struct.unpack('>I', d[off + 4:off + 8])[0]
seg = d[off:off + fdt_total]
print(f'  FDT at 0x{off:x} totalsize={fdt_total}  match_header={fdt_total == dtb_size}')
for name, pat in {
    '383MHz': b'\x00\x00\x00\x00\x16\xd4\x1d\xc0',
    '200MHz': b'\x00\x00\x00\x00\x0b\xeb\xc2\x00',
    '470MHz': b'\x00\x00\x00\x00\x1c\x03\xa1\x80',
    '560MHz': b'\x00\x00\x00\x00\x21\x60\xec\x00',
}.items():
    print(f'    {name}: {"present" if pat in seg else "absent"}')
print(f'  table+bootconfig bytes: {len(d) - (off + ((fdt_total + page - 1)//page)*page)}')

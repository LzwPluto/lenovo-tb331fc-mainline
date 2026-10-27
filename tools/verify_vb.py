#!/usr/bin/env python3
"""verify_vb.py - sanity check a repacked vendor_boot image."""
import struct
import sys

p = sys.argv[1]
d = open(p, 'rb').read()

assert d[:8] == b'VNDRBOOT', 'not a vendor_boot image'
page = struct.unpack_from('<I', d, 0x0C)[0]
vr_size = struct.unpack_from('<I', d, 0x18)[0]
dtb_size = struct.unpack_from('<I', d, 0x1C)[0]
dtb_addr = struct.unpack_from('<Q', d, 0x20)[0]

hdr_size = struct.unpack_from('<I', d, 0x830)[0]

print(f'page          = {page}')
print(f'vendor_ramdisk= {vr_size} bytes')
print(f'dtb_size(hdr) = {dtb_size}')

off = -1
for cand in range(0, len(d) - 4, page):
    if d[cand:cand + 4] == b'\xd0\x0d\xfe\xed':
        off = cand
        break
if off < 0:
    sys.exit('no FDT found')

fdt_total = struct.unpack('>I', d[off + 4:off + 8])[0]
print(f'FDT at 0x{off:x}, totalsize {fdt_total}')
seg = d[off:off + fdt_total]

checks = {
    '383000000 (0x16d41dc0)': b'\x00\x00\x00\x00\x16\xd4\x1d\xc0',
    '200000000 (0x0bebc200)': b'\x00\x00\x00\x00\x0b\xeb\xc2\x00',
    '384000000 (0x16e36000)': b'\x00\x00\x00\x00\x16\xe3\x60\x00',
    '470000000 (0x1c03a180)': b'\x00\x00\x00\x00\x1c\x03\xa1\x80',
    '560000000 (0x2160ec00)': b'\x00\x00\x00\x00\x21\x60\xec\x00',
}
for name, pat in checks.items():
    print(f'  {name}: {"present" if pat in seg else "absent"}')

# __symbols__ present?
print(f'  __symbols__ string in FDT: {"yes" if b"__symbols__" in seg else "NO"}')

ok = (fdt_total == dtb_size)
print(f'header dtb_size == FDT totalsize: {ok}')

# tail (table + bootconfig) should start at the page after the dtb
tail_off = off + ((fdt_total + page - 1) // page) * page
print(f'tail starts at 0x{tail_off:x}, image size 0x{len(d):x}, tail bytes {len(d)-tail_off}')

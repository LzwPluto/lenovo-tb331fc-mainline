#!/usr/bin/env python3
"""repack_vb_dtb2.py - swap the DTB inside a vendor_boot image correctly.

Layout of the images we build (and of the user's quiet build):
    page | vendor_ramdisk | dtb (page aligned) | vendor_ramdisk_table | bootconfig
The table sits on the page boundary *after* the dtb, so simply appending it
right behind the old dtb_size corrupts it.  This version locates the dtb by its
FDT magic, keeps everything from the next page boundary onwards verbatim, and
only updates dtb_size in the header.
"""
import struct
import sys

vb_path, dtb_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

vb = bytearray(open(vb_path, 'rb').read())
dtb = open(dtb_path, 'rb').read()
FDT = b'\xd0\x0d\xfe\xed'

if vb[:8] != b'VNDRBOOT':
    sys.exit('not a vendor_boot image')

page = struct.unpack_from('<I', vb, 0x0C)[0]
vr_size = struct.unpack_from('<I', vb, 0x18)[0]
hdr_size = struct.unpack_from('<I', vb, 0x830)[0]
old_dtb_size = struct.unpack_from('<I', vb, 0x834)[0]
table_size = struct.unpack_from('<I', vb, 0x840)[0]

# find the dtb section (first FDT magic after the vendor_ramdisk)
search_from = page + ((vr_size + page - 1) // page) * page
dtb_off = vb.find(FDT, search_from)
if dtb_off < 0:
    sys.exit('DTB not found')
if dtb_off % page:
    print(f'note: dtb offset 0x{dtb_off:x} is not page aligned')

# everything from the next page boundary after the old dtb is the tail
tail_off = ((dtb_off + old_dtb_size + page - 1) // page) * page
tail = bytes(vb[tail_off:])

print(f'page           = {page}')
print(f'vendor_ramdisk = {vr_size} bytes @ 0x{page:x}')
print(f'dtb            = 0x{dtb_off:x}, old {old_dtb_size} -> new {len(dtb)}')
print(f'table_size     = {table_size}')
print(f'tail from      = 0x{tail_off:x} ({len(tail)} bytes)')

out = bytearray(vb[:dtb_off])
out += dtb
out += b'\0' * (((len(out) + page - 1) // page) * page - len(out))
assert len(out) % page == 0
out += tail
struct.pack_into('<I', out, 0x834, len(dtb))

open(out_path, 'wb').write(out)
print(f'wrote {out_path}: {len(out)} bytes')

# verification
chk = open(out_path, 'rb').read()
assert chk[:8] == b'VNDRBOOT'
assert struct.unpack_from('<I', chk, 0x834)[0] == len(dtb)
assert chk[dtb_off:dtb_off + 4] == FDT
assert struct.unpack_from('<I', chk, dtb_off + 4)[0] == len(dtb), 'FDT totalsize != header'
tbl = ((dtb_off + len(dtb) + page - 1) // page) * page
print(f'table now at 0x{tbl:x}: size={struct.unpack_from("<I", chk, tbl)[0]} '
      f'offset={struct.unpack_from("<I", chk, tbl+4)[0]} '
      f'type={struct.unpack_from("<I", chk, tbl+8)[0]}')
assert struct.unpack_from('<I', chk, tbl)[0] == vr_size, 'table size field mismatch'
print('sanity OK')

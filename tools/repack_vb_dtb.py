#!/usr/bin/env python3
"""repack_vb_dtb.py - swap the DTB inside a vendor_boot image, keeping the
vendor_ramdisk (initramfs with firmware) and cmdline untouched.

Usage: repack_vb_dtb.py <in_vb.img> <new.dtb> <out_vb.img>
"""
import struct
import sys

vb_path, dtb_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

vb = bytearray(open(vb_path, 'rb').read())
dtb = open(dtb_path, 'rb').read()

if vb[:8] != b'VNDRBOOT':
    sys.exit('not a vendor_boot image')

hdr_ver = struct.unpack_from('<I', vb, 0x08)[0]
page = struct.unpack_from('<I', vb, 0x0C)[0]
vr_size = struct.unpack_from('<I', vb, 0x18)[0]
cmdline = vb[0x1C:0x1C + 2048].split(b'\0')[0].decode()
hdr_size = struct.unpack_from('<I', vb, 0x830)[0]
old_dtb_size = struct.unpack_from('<I', vb, 0x834)[0]
dtb_addr = struct.unpack_from('<Q', vb, 0x838)[0]
table_size = struct.unpack_from('<I', vb, 0x840)[0]
entry_num = struct.unpack_from('<I', vb, 0x844)[0]
entry_size = struct.unpack_from('<I', vb, 0x848)[0]
bc_size = struct.unpack_from('<I', vb, 0x84C)[0]

print(f'header_version = {hdr_ver}, page = {page}')
print(f'cmdline        = {cmdline}')
print(f'vendor_ramdisk = {vr_size} bytes')
print(f'old dtb_size   = {old_dtb_size} / new = {len(dtb)}')
print(f'dtb_addr       = 0x{dtb_addr:x}')

# find the dtb section position: sections are page aligned, in order
# vendor_ramdisk, [dtb], [table], [bootconfig]
off = page
vr_off = off
off += (vr_size + page - 1) // page * page

# The DTB may come before or after the table; locate it by searching for the
# FDT magic near the expected place.
FDT = b'\xd0\x0d\xfe\xed'
dtb_off = None
for cand in (off, off + (table_size + page - 1) // page * page):
    if vb[cand:cand + 4] == FDT:
        dtb_off = cand
        break
if dtb_off is None:
    # fall back: scan the tail
    idx = vb.find(FDT, off)
    if idx < 0:
        sys.exit('DTB section not found')
    dtb_off = idx
print(f'dtb section at 0x{dtb_off:x}')

# rebuild: everything up to dtb_off, new dtb, then any sections that followed
# (table / bootconfig) - recompute their new position
after = bytearray()
if table_size:
    tbl = vb[dtb_off + old_dtb_size:dtb_off + old_dtb_size + table_size]
    after += tbl
    after += b'\0' * ((page - len(after) % page) % page)
if bc_size:
    bc = vb[dtb_off + old_dtb_size + table_size:
            dtb_off + old_dtb_size + table_size + bc_size]
    after += bc

out = bytearray(vb[:dtb_off])
out += dtb
out += b'\0' * ((page - len(out) % page) % page)
out += after
out += b'\0' * ((page - len(out) % page) % page)

struct.pack_into('<I', out, 0x834, len(dtb))

open(out_path, 'wb').write(out)
print(f'wrote {out_path}: {len(out)} bytes')

# sanity check
chk = open(out_path, 'rb').read()
assert chk[:8] == b'VNDRBOOT'
assert struct.unpack_from('<I', chk, 0x834)[0] == len(dtb)
assert chk[dtb_off:dtb_off + 4] == FDT
print('sanity OK: header dtb_size matches, FDT magic in place')

#!/usr/bin/env python3
"""strip_rndis.py - remove the RNDIS function from the gadget inside a
vendor_boot image, leaving only the CDC-ACM serial console.

Windows 11 no longer ships an RNDIS driver, so a composite ACM+RNDIS gadget
makes the host retry enumeration forever; the whole device (including the ACM
serial port we rely on) keeps dropping with "unknown USB device".  ACM alone is
stable, and we have wlan0 for networking now.

Usage: strip_rndis.py <in_vb.img> <out_vb.img>
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile

src, dst = sys.argv[1], sys.argv[2]
d = bytearray(open(src, 'rb').read())
assert d[:8] == b'VNDRBOOT', 'not vendor_boot'

page = struct.unpack_from('<I', d, 0x0C)[0]
vr_size = struct.unpack_from('<I', d, 0x18)[0]
hdr_size = struct.unpack_from('<I', d, 0x830)[0]
dtb_size = struct.unpack_from('<I', d, 0x834)[0]

cmdline = d[0x1C:0x1C + 2048].split(b'\0')[0].decode()
vr = bytes(d[page:page + vr_size])
print(f'ramdisk {vr_size} bytes, dtb {dtb_size} bytes')
print(f'cmdline: {cmdline[:120]}...')

tmp = tempfile.mkdtemp()
cpio = os.path.join(tmp, 'in.cpio')
open(cpio, 'wb').write(vr)

work = os.path.join(tmp, 'rd')
os.makedirs(work)
subprocess.run(['cpio', '-idmv', '--quiet'], stdin=open(cpio, 'rb'),
               cwd=work, check=True,
               env={**os.environ, 'LC_ALL': 'C'})

# find gadget.sh
gs = None
for root, _dirs, files in os.walk(work):
    if 'gadget.sh' in files:
        gs = os.path.join(root, 'gadget.sh')
        break
if not gs:
    sys.exit('gadget.sh not found in initramfs')

print(f'patching {gs}')
txt = open(gs, encoding='utf-8').read()

# comment out every rndis-related line
out = []
for line in txt.split('\n'):
    s = line.strip()
    if 'rndis' in s.lower() and not s.startswith('#'):
        out.append('# [rndis removed: Win11 has no RNDIS driver] ' + line)
    else:
        out.append(line)
open(gs, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))

newcpio = os.path.join(tmp, 'out.cpio')
listing = subprocess.run(['find', '.', '-print'], cwd=work, capture_output=True,
                         text=True, check=True).stdout
with open(newcpio, 'wb') as fh:
    subprocess.run(['cpio', '-o', '-H', 'newc'], cwd=work,
                   input=listing.encode(), stdout=fh, check=True,
                   stderr=subprocess.DEVNULL)
print(f'new cpio {os.path.getsize(newcpio)} bytes')

# rebuild: header + ramdisk + dtb + table + bootconfig (copy tail verbatim)
off = -1
for cand in range(0, len(d) - 4, page):
    if d[cand:cand + 4] == b'\xd0\x0d\xfe\xed':
        off = cand
        break
fdt_total = struct.unpack('>I', d[off + 4:off + 8])[0]
dtb = d[off:off + fdt_total]
tail_start = off + ((fdt_total + page - 1) // page) * page
tail = d[tail_start:]

newrd = open(newcpio, 'rb').read()
out_img = bytearray(d[:page])          # keep header
out_img += newrd
pad = (-len(out_img)) % page
out_img += b'\0' * pad
out_img += dtb
pad = (-len(out_img)) % page
out_img += b'\0' * pad
out_img += tail

out_img = bytearray(out_img)
struct.pack_into('<I', out_img, 0x18, len(newrd))
struct.pack_into('<I', out_img, 0x834, len(dtb))
open(dst, 'wb').write(bytes(out_img))
print(f'wrote {dst}: {len(out_img)} bytes')
shutil.rmtree(tmp)

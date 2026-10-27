#!/usr/bin/env python3
"""Hexdump the boot header tail + scan for FDT magic anywhere in the image."""
import struct, sys

FDT = struct.pack('>I', 0xd00dfeed)
GZIP = b'\x1f\x8b\x08'


def hexdump(data, start, length, width=16):
    out = []
    for i in range(0, length, width):
        chunk = data[start + i:start + i + width]
        if not chunk:
            break
        hx = ' '.join(f'{b:02x}' for b in chunk)
        asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        out.append(f'  {start+i:08x}  {hx:<{width*3}}  {asc}')
    return '\n'.join(out)


for path in sys.argv[1:]:
    data = open(path, 'rb').read()
    print('=' * 78)
    print(f'FILE {path}  size=0x{len(data):x} ({len(data)})')
    print('--- header 0x0000..0x0060 ---')
    print(hexdump(data, 0, 0x60))
    print('--- header tail 0x640..0x6b0 (recovery_dtbo / header_size / dtb_size / dtb_addr) ---')
    print(hexdump(data, 0x640, 0x70))
    print('  field map per bootimg.h v2:')
    for name, off, fmt in (('recovery_dtbo_size', 1632, '<I'), ('recovery_dtbo_offset', 1640, '<Q'),
                           ('header_size', 1648, '<I'), ('dtb_size', 1652, '<I'), ('dtb_addr', 1656, '<Q')):
        v = struct.unpack_from(fmt, data, off)[0]
        print(f'    +{off:4d} (0x{off:04x}) {name:22s} = 0x{v:x} ({v})')
    print('  --- raw u32 sweep 0x660..0x690 ---')
    for off in range(0x660, 0x690, 4):
        v = struct.unpack_from('<I', data, off)[0]
        print(f'    +0x{off:03x} = 0x{v:08x} ({v})')
    print('  --- FDT / gzip scan ---')
    pos = 0
    fdt_hits = []
    while True:
        i = data.find(FDT, pos)
        if i < 0:
            break
        fdt_hits.append(i)
        pos = i + 4
    print(f'    FDT magic hits: {[hex(x) for x in fdt_hits[:20]]}  (total {len(fdt_hits)})')
    for i in fdt_hits[:10]:
        if i + 8 <= len(data):
            tot = struct.unpack_from('>I', data, i + 4)[0]
            print(f'      @0x{i:x} totalsize={tot} (0x{tot:x}) end=0x{i+tot:x}')
    pos = 0
    gz = []
    while True:
        i = data.find(GZIP, pos)
        if i < 0:
            break
        gz.append(i)
        pos = i + 3
    print(f'    gzip hits: {[hex(x) for x in gz[:10]]} (total {len(gz)})')
    # where does real content end?
    tail = data[-64:]
    print(f'    last 64 bytes: {tail.hex()}')
    print()

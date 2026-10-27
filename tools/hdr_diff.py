#!/usr/bin/env python3
"""Field-by-field diff of two boot / vendor_boot v4 images against factory.

Since the factory images are ground truth (ABL accepts them), every differing
field is a bisection candidate -- and we get them all in one shot, no flashing.
"""
import struct, sys

BOOT_V4_FIELDS = [
    ('magic', 0, 8, 'bytes'),
    ('kernel_size', 0x008, 4, 'u32'),
    ('ramdisk_size', 0x00c, 4, 'u32'),
    ('os_version', 0x010, 4, 'u32'),
    ('header_size', 0x014, 4, 'u32'),
    ('reserved0', 0x018, 4, 'u32'),
    ('reserved1', 0x01c, 4, 'u32'),
    ('reserved2', 0x020, 4, 'u32'),
    ('reserved3', 0x024, 4, 'u32'),
    ('header_version', 0x028, 4, 'u32'),
    ('cmdline[0:64]', 0x02c, 64, 'bytes'),
]

VB_V4_FIELDS = [
    ('magic', 0x000, 8, 'bytes'),
    ('header_version', 0x008, 4, 'u32'),
    ('page_size', 0x00c, 4, 'u32'),
    ('kernel_addr', 0x010, 4, 'u32'),
    ('ramdisk_addr', 0x014, 4, 'u32'),
    ('vendor_ramdisk_size', 0x018, 4, 'u32'),
    ('cmdline[0:64]', 0x01c, 64, 'bytes'),
    ('cmdline[2047]', 0x81b, 1, 'bytes'),
    ('tags_addr', 0x81c, 4, 'u32'),
    ('name[0:16]', 0x820, 16, 'bytes'),
    ('header_size', 0x830, 4, 'u32'),
    ('dtb_size', 0x834, 4, 'u32'),
    ('dtb_addr', 0x838, 8, 'u64'),
    ('vendor_ramdisk_table_size', 0x840, 4, 'u32'),
    ('vendor_ramdisk_table_entry_num', 0x844, 4, 'u32'),
    ('vendor_ramdisk_table_entry_size', 0x848, 4, 'u32'),
    ('bootconfig_size', 0x84c, 4, 'u32'),
]


def val(d, off, ln, kind):
    if off + ln > len(d):
        return '(beyond)'
    raw = d[off:off + ln]
    if kind == 'u32':
        return hex(struct.unpack('<I', raw)[0])
    if kind == 'u64':
        return hex(struct.unpack('<Q', raw)[0])
    if off == 0x0 and ln == 8:
        return raw.decode('ascii', 'replace')
    return raw.hex()


def diff(name, a_path, b_path, fields):
    a = open(a_path, 'rb').read()
    b = open(b_path, 'rb').read()
    print(f'\n===== {name} =====')
    print(f'  factory : {a_path}  ({len(a)} bytes)')
    print(f'  ours    : {b_path}  ({len(b)} bytes)')
    ndiff = 0
    for fname, off, ln, kind in fields:
        va, vb = val(a, off, ln, kind), val(b, off, ln, kind)
        mark = '   ' if va == vb else '>>>'
        if va != vb:
            ndiff += 1
        print(f'  {mark} {fname:32s} factory={va:<34s} ours={vb}')
    print(f'  --- {ndiff} differing field(s)')


def table_dump(path, off, label):
    d = open(path, 'rb').read()
    if off + 108 > len(d):
        print(f'  {label}: no table at 0x{off:x}')
        return
    t = d[off:off + 108]
    sz, o, ty = struct.unpack_from('<3I', t, 0)
    nm = t[0x0c:0x2c].split(b'\0')[0].decode('ascii', 'replace')
    bid = struct.unpack_from('<16I', t, 0x2c)
    print(f'  {label}: size={sz} offset={o} type={ty} name="{nm}"')
    print(f'         board_id={[hex(x) for x in bid]}')


if __name__ == '__main__':
    fw = r'D:\TB331FC_GSI_Kit\08_一键刷机\fw'
    bd = r'D:\TB331FCLinux\build'
    diff('boot v4 header', fw + r'\boot.img', bd + r'\v4_boot_b.img', BOOT_V4_FIELDS)
    diff('init_boot v4 header', fw + r'\init_boot.img', bd + r'\v4_init_boot_b.img', BOOT_V4_FIELDS)
    diff('vendor_boot v4 header', fw + r'\vendor_boot.img', bd + r'\v4_vendor_boot_b.img', VB_V4_FIELDS)
    print('\n===== vendor_ramdisk_table content =====')
    table_dump(fw + r'\vendor_boot.img', 0xB19000, 'factory @0xB19000')
    table_dump(bd + r'\v4_vendor_boot_b.img', 0x2000, 'ours    @0x2000')

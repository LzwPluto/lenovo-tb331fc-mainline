#!/usr/bin/env python3
"""Android boot / init_boot / vendor_boot header parser (v0-v4).

Layout notes (these are the *packed* struct definitions used by mkbootimg;
this is where hand-written parsers usually go wrong):

  boot_img_hdr v0-v2  (packed, NO 8-byte alignment)
    0x000 magic[8]
    0x008 kernel_size  u32
    0x00c kernel_addr  u32
    0x010 ramdisk_size u32
    0x014 ramdisk_addr u32
    0x018 second_size  u32
    0x01c second_addr  u32
    0x020 tags_addr    u32
    0x024 page_size    u32
    0x028 header_version u32
    0x02c os_version   u32
    0x030 name[16]
    0x040 cmdline[512]
    0x240 id[8]
    0x260 extra_cmdline[1024]
    0x660 recovery_dtbo_size   u32      (v1+)
    0x664 recovery_dtbo_offset u64      (v1+)  <-- NOT 8-byte aligned
    0x66c header_size          u32      (v1+)
    0x670 dtb_size             u32      (v2+)
    0x674 dtb_addr             u64      (v2+)  <-- NOT 8-byte aligned
    total 0x67c = 1660

  boot_img_hdr v3/v4
    0x000 magic[8]
    0x008 kernel_size u32
    0x00c ramdisk_size u32
    0x010 os_version u32
    0x014 header_size u32
    0x018 reserved[4]
    0x028 header_version u32
    0x02c cmdline[1536]
    total 1580, padded to 1584

Sections always start at page_size-aligned offsets, page 0 being the header.
"""
import struct, sys, hashlib, os

FDT_MAGIC = 0xd00dfeed


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def u64(b, o):
    return struct.unpack_from('<Q', b, o)[0]


def cstr(raw):
    return raw.split(b'\0')[0].decode('ascii', 'replace')


def align(n, p):
    return (n + p - 1) // p * p


def parse_boot(data):
    if data[:8] != b'ANDROID!':
        return None
    h = {'magic': 'ANDROID!', 'header_version': u32(data, 0x28)}
    v = h['header_version']
    if v >= 3:
        h['kernel_size'] = u32(data, 0x08)
        h['ramdisk_size'] = u32(data, 0x0c)
        h['os_version'] = u32(data, 0x10)
        h['header_size'] = u32(data, 0x14)
        h['cmdline'] = cstr(data[0x2c:0x2c + 1536])
        h['page_size'] = 4096
        hdr_end = max(h['header_size'], 1580)
    else:
        h['kernel_size'] = u32(data, 0x08)
        h['kernel_addr'] = u32(data, 0x0c)
        h['ramdisk_size'] = u32(data, 0x10)
        h['ramdisk_addr'] = u32(data, 0x14)
        h['second_size'] = u32(data, 0x18)
        h['second_addr'] = u32(data, 0x1c)
        h['tags_addr'] = u32(data, 0x20)
        h['page_size'] = u32(data, 0x24)
        h['os_version'] = u32(data, 0x2c)
        h['name'] = cstr(data[0x30:0x40])
        h['cmdline'] = cstr(data[0x40:0x240])
        h['extra_cmdline'] = cstr(data[0x260:0x660])
        hdr_end = 1632
        if v >= 1:
            h['recovery_dtbo_size'] = u32(data, 0x660)
            h['recovery_dtbo_offset'] = u64(data, 0x664)
            h['header_size'] = u32(data, 0x66c)
            hdr_end = max(h['header_size'], 0x66c)
        if v >= 2:
            h['dtb_size'] = u32(data, 0x670)
            h['dtb_addr'] = u64(data, 0x674)
    ps = h['page_size'] if h['page_size'] in (2048, 4096, 8192, 16384, 65536) else 4096
    sec = {}
    off = align(hdr_end, ps)
    sec['kernel'] = (off, h['kernel_size']);  off += align(h['kernel_size'], ps)
    sec['ramdisk'] = (off, h['ramdisk_size']); off += align(h['ramdisk_size'], ps)
    sec['second'] = (off, h.get('second_size', 0)); off += align(h.get('second_size', 0), ps)
    if v >= 1 and h.get('recovery_dtbo_size'):
        sec['recovery_dtbo'] = (off, h['recovery_dtbo_size'])
        off += align(h['recovery_dtbo_size'], ps)
    if v >= 2 and h.get('dtb_size'):
        sec['dtb'] = (off, h['dtb_size'])
        off += align(h['dtb_size'], ps)
    h['_sections'] = sec
    h['_end'] = off
    return h


def parse_vendor_boot(data):
    if data[:8] != b'VNDRBOOT':
        return None
    h = {'magic': 'VNDRBOOT'}
    h['header_version'] = u32(data, 0x08)
    h['page_size'] = u32(data, 0x0c)
    h['kernel_addr'] = u32(data, 0x10)
    h['ramdisk_addr'] = u32(data, 0x14)
    h['vendor_ramdisk_size'] = u32(data, 0x18)
    h['cmdline'] = cstr(data[0x1c:0x1c + 2048])
    h['tags_addr'] = u32(data, 0x81c)
    h['name'] = cstr(data[0x820:0x830])
    h['header_size'] = u32(data, 0x830)
    h['dtb_size'] = u32(data, 0x834)
    h['dtb_addr'] = u64(data, 0x838)
    if h['header_version'] >= 4:
        h['vendor_ramdisk_table_size'] = u32(data, 0x840)
        h['vendor_ramdisk_table_entry_num'] = u32(data, 0x844)
        h['vendor_ramdisk_table_entry_size'] = u32(data, 0x848)
        h['bootconfig_size'] = u32(data, 0x84c)
    ps = h['page_size'] if h['page_size'] in (2048, 4096, 8192, 16384, 65536) else 4096
    sec = {}
    off = align(max(h['header_size'], 0x840), ps)
    sec['vendor_ramdisk'] = (off, h['vendor_ramdisk_size'])
    off += align(h['vendor_ramdisk_size'], ps)
    if h['header_version'] >= 4 and h.get('vendor_ramdisk_table_size'):
        sec['vendor_ramdisk_table'] = (off, h['vendor_ramdisk_table_size'])
        off += align(h['vendor_ramdisk_table_size'], ps)
    if h.get('dtb_size'):
        sec['dtb'] = (off, h['dtb_size'])
        off += align(h['dtb_size'], ps)
    if h['header_version'] >= 4 and h.get('bootconfig_size'):
        sec['bootconfig'] = (off, h['bootconfig_size'])
        off += align(h['bootconfig_size'], ps)
    h['_sections'] = sec
    h['_end'] = off
    return h


def fdt_root_props(blob):
    if len(blob) < 40 or struct.unpack_from('>I', blob, 0)[0] != FDT_MAGIC:
        return None
    off_struct = struct.unpack_from('>I', blob, 8)[0]
    off_strings = struct.unpack_from('>I', blob, 12)[0]
    p = off_struct
    if struct.unpack_from('>I', blob, p)[0] != 1:
        return None
    p += 4
    while blob[p] != 0:
        p += 1
    p = (p + 4) & ~3
    props = {}
    while p + 4 <= len(blob):
        tag = struct.unpack_from('>I', blob, p)[0]; p += 4
        if tag in (1, 2, 9):
            break
        if tag == 4:
            continue
        if tag == 3:
            ln, nameoff = struct.unpack_from('>II', blob, p); p += 8
            val = blob[p:p + ln]; p = (p + ln + 3) & ~3
            end = blob.find(b'\0', off_strings + nameoff)
            props[blob[off_strings + nameoff:end].decode('ascii', 'replace')] = val
    return props


def show_props(props, ind='      '):
    if props is None:
        print(f'{ind}(not an FDT)')
        return
    for k in ('model', 'compatible', 'qcom,msm-id', 'qcom,board-id', 'qcom,pmic-id'):
        if k in props:
            v = props[k]
            if k in ('model', 'compatible'):
                print(f'{ind}{k:14s} = {v.split(bytes([0]))[0].decode("ascii","replace")}')
            elif len(v) % 4 == 0:
                ints = struct.unpack(f'>{len(v)//4}I', v)
                print(f'{ind}{k:14s} = ' + ' '.join(f'<0x{x:x}>' for x in ints))
            else:
                print(f'{ind}{k:14s} = {v.hex()}')


def report(path, extract_dir=None):
    data = open(path, 'rb').read()
    print('=' * 78)
    print(f'FILE {path}\n  size = {len(data)} (0x{len(data):x})   md5 = {hashlib.md5(data).hexdigest()}')
    h = parse_boot(data)
    v = None if h else parse_vendor_boot(data)
    if h:
        print('  --- boot header ---')
        for k, val in h.items():
            if k.startswith('_'):
                continue
            if isinstance(val, int) and val > 0xffff:
                print(f'    {k:24s} = {val} (0x{val:x})')
            else:
                print(f'    {k:24s} = {val}')
        print('  --- sections (page-aligned, as ABL computes them) ---')
        for name, (off, size) in h['_sections'].items():
            tag = ''
            if off + size > len(data):
                tag = '   <-- BEYOND FILE END'
            print(f'    {name:14s} off=0x{off:<8x} size={size:<10d} end=0x{off+size:<8x}{tag}')
            if size and off + size <= len(data):
                blob = data[off:off + size]
                if name == 'kernel':
                    kind = ('GZIP' if blob[:2] == b'\x1f\x8b' else
                            'LZ4' if blob[:4] == b'\x04\x22\x4d\x18' else
                            'raw Image' if blob[0x38:0x3c] == b'ARMd' else 'raw/unknown')
                    print(f'        kernel: {kind}   first8={blob[:8].hex()}')
                    if kind == 'raw Image':
                        print(f'        ARM64 Image: text_offset=0x{u64(blob,8):x} '
                              f'image_size=0x{u64(blob,16):x} flags=0x{u64(blob,24):x}')
                if name == 'dtb':
                    tot = struct.unpack_from('>I', blob, 4)[0] if len(blob) >= 8 else 0
                    print(f'        FDT: magic={"OK" if blob[:4] == struct.pack(">I", FDT_MAGIC) else blob[:4].hex()} '
                          f'totalsize={tot} (0x{tot:x})')
                    show_props(fdt_root_props(blob))
                    if extract_dir:
                        out = os.path.join(extract_dir, os.path.basename(path) + '.dtb')
                        open(out, 'wb').write(blob[:tot] if tot else blob)
                        print(f'        -> extracted {out}')
        print(f'  image occupies up to 0x{h["_end"]:x} of 0x{len(data):x}')
    elif v:
        print('  --- vendor_boot header ---')
        for k, val in v.items():
            if k.startswith('_'):
                continue
            if isinstance(val, int) and val > 0xffff:
                print(f'    {k:32s} = {val} (0x{val:x})')
            else:
                print(f'    {k:32s} = {val}')
        print('  --- sections ---')
        for name, (off, size) in v['_sections'].items():
            tag = '   <-- BEYOND FILE END' if off + size > len(data) else ''
            print(f'    {name:22s} off=0x{off:<8x} size={size:<10d}{tag}')
        if 'dtb' in v['_sections']:
            off, size = v['_sections']['dtb']
            blob = data[off:off + size]
            n = 0
            pos = 0
            while True:
                i = blob.find(struct.pack('>I', FDT_MAGIC), pos)
                if i < 0:
                    break
                n += 1
                pos = i + 4
            print(f'    -> {n} FDT magic hit(s); first blob:')
            show_props(fdt_root_props(blob), '       ')
        if 'bootconfig' in v['_sections']:
            off, size = v['_sections']['bootconfig']
            print('  --- bootconfig ---')
            print('    ' + data[off:off + size].decode('ascii', 'replace').replace('\n', '\n    '))
    else:
        print(f'  UNKNOWN type; first32={data[:32].hex()}')
    print()


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    ed = None
    if '-o' in sys.argv:
        ed = sys.argv[sys.argv.index('-o') + 1]
        os.makedirs(ed, exist_ok=True)
    for p in args:
        if p == ed:
            continue
        report(p, ed)

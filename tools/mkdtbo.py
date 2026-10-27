#!/usr/bin/env python3
"""mkdtbo.py - rebuild a Qualcomm dtbo container keeping only chosen entries.

Container layout (little-endian, verified against the factory dtbo.img):
  0x00 magic            0xd7b7ab1e
  0x04 total_size
  0x08 header_size      0x20
  0x0c dt_entries_offset
  0x10 dt_entry_count
  0x14 dt_entry_size    0x20
  0x18 page_size
  0x1c version

  entry (0x20 bytes): size u32, offset u32, id u32, rev u32, custom[4]

Usage:
  mkdtbo.py --src dtbo.img --list
  mkdtbo.py --src dtbo.img --entries 2 --out only2.img
"""
import argparse, struct, os

PAGE = 4096
FDT = struct.pack('>I', 0xd00dfeed)


def align(n, p=PAGE):
    return (n + p - 1) // p * p


def fdt_root_keys(blob):
    if blob[:4] != FDT:
        return None
    off_struct = struct.unpack_from('>I', blob, 8)[0]
    off_strings = struct.unpack_from('>I', blob, 12)[0]
    p = off_struct
    if struct.unpack_from('>I', blob, p)[0] != 1:
        return None
    p += 4
    while p < len(blob) and blob[p] != 0:
        p += 1
    p = (p + 4) & ~3
    props = {}
    while p + 4 <= len(blob):
        t = struct.unpack_from('>I', blob, p)[0]; p += 4
        if t in (1, 2, 9):
            break
        if t == 4:
            continue
        if t == 3:
            ln, no = struct.unpack_from('>II', blob, p); p += 8
            v = blob[p:p + ln]; p = (p + ln + 3) & ~3
            e = blob.find(b'\0', off_strings + no)
            props[blob[off_strings + no:e].decode('ascii', 'replace')] = v
    return props


def parse(path):
    d = open(path, 'rb').read()
    magic, total, hdrsz, eoff, cnt, esz = struct.unpack_from('>6I', d, 0)
    assert magic == 0xd7b7ab1e, hex(magic)
    ents = []
    for n in range(cnt):
        b = eoff + n * esz
        sz, off, eid, rev = struct.unpack_from('>4I', d, b)
        ents.append({'n': n, 'size': sz, 'off': off, 'id': eid, 'rev': rev,
                     'raw': d[b:b + esz], 'data': d[off:off + sz]})
    return d, dict(magic=magic, hdrsz=hdrsz, eoff=eoff, esz=esz,
                   page=struct.unpack_from('>I', d, 0x18)[0],
                   ver=struct.unpack_from('>I', d, 0x1c)[0]), ents


def describe(ents):
    DEV_MSM = [0x206, 0x10000]
    DEV_BRD = [0x10022, 0x0]
    print(f'{"#":>3} {"size":>8}  {"model":<46} msm-id / board-id / pmic-id            MATCH')
    for e in ents:
        props = fdt_root_keys(e['data']) or {}
        model = props.get('model', b'?').split(b'\0')[0].decode('ascii', 'replace')[:46]
        mi = props.get('qcom,msm-id')
        bi = props.get('qcom,board-id')
        pi = props.get('qcom,pmic-id')
        mi = list(struct.unpack(f'>{len(mi)//4}I', mi)) if mi else []
        bi = list(struct.unpack(f'>{len(bi)//4}I', bi)) if bi else []
        pi = list(struct.unpack(f'>{len(pi)//4}I', pi)) if pi else []
        ok = mi[:2] == DEV_MSM and bi[:2] == DEV_BRD
        print(f'{e["n"]:>3} {e["size"]:>8}  {model:<46} '
              f'{[hex(x) for x in mi]} {[hex(x) for x in bi]} {[hex(x) for x in pi]}  '
              f'{"<== MATCH" if ok else ""}')


def build(src, keep, out):
    d, hdr, ents = parse(src)
    sel = [e for e in ents if e['n'] in keep]
    assert sel, 'no entries selected'
    esz = hdr['esz']
    tbl_end = hdr['eoff'] + len(sel) * esz
    cur = align(tbl_end, hdr['page'])
    offsets = []
    for e in sel:
        cur = align(cur, hdr['page'])
        offsets.append(cur)
        cur += e['size']
    total = max(offsets[-1] + sel[-1]['size'], hdr['hdrsz'])

    buf = bytearray(total)
    struct.pack_into('>I', buf, 0x00, hdr['magic'])
    struct.pack_into('>I', buf, 0x04, total)
    struct.pack_into('>I', buf, 0x08, hdr['hdrsz'])
    struct.pack_into('>I', buf, 0x0c, hdr['eoff'])
    struct.pack_into('>I', buf, 0x10, len(sel))
    struct.pack_into('>I', buf, 0x14, esz)
    struct.pack_into('>I', buf, 0x18, hdr['page'])
    struct.pack_into('>I', buf, 0x1c, hdr['ver'])
    for i, e in enumerate(sel):
        b = hdr['eoff'] + i * esz
        buf[b:b + esz] = e['raw']
        struct.pack_into('>I', buf, b + 0x04, offsets[i])
        buf[offsets[i]:offsets[i] + e['size']] = e['data']
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    open(out, 'wb').write(bytes(buf))
    print(f'\nwrote {out}: {total} bytes, {len(sel)} entry(ies) '
          f'[{[e["n"] for e in sel]}]')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--entries', default='')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    d, hdr, ents = parse(a.src)
    if a.list or not a.entries:
        print(f'{a.src}: {len(ents)} entries  hdrsz=0x{hdr["hdrsz"]:x} '
              f'eoff=0x{hdr["eoff"]:x} esz=0x{hdr["esz"]:x} page=0x{hdr["page"]:x}')
        describe(ents)
    if a.entries:
        keep = {int(x) for x in a.entries.split(',')}
        build(a.src, keep, a.out or 'dtbo_sel.img')

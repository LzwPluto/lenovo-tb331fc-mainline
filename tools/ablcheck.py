#!/usr/bin/env python3
"""ablcheck.py - offline conformance check for TB331FC (khaje / SM6225-AD).

Replays the hard checks Qualcomm ABL performs on a boot set BEFORE you spend a
flash cycle on it.  Every check below is derived from LinuxLoader.efi
(D:\\TB331FC_GSI_Kit\\LinuxLoader.efi) and the on-device partition table
(`fastboot getvar all`).

Usage:
  ablcheck.py --boot boot.img [--init-boot init_boot.img]
              [--vendor-boot vendor_boot.img] [--dtbo dtbo.img]

Exit code 0 = all hard checks pass.
"""
import struct, sys, os, argparse

FDT_MAGIC = struct.pack('>I', 0xd00dfeed)
DTBO_MAGIC = 0xd7b7ab1e

# ---- from fastboot getvar all -------------------------------------------------
PART = {'boot': 0x6000000, 'init_boot': 0x800000, 'vendor_boot': 0x6000000,
        'dtbo': 0x1800000, 'vbmeta': 0x10000}
DEVICE = {'msm-id': [0x206, 0x10000], 'board-id': [0x10022, 0x0]}

OK, WARN, ERR = 'PASS', 'WARN', 'FAIL'
results = []


def chk(level, name, detail=''):
    results.append((level, name, detail))
    print(f'  [{level}] {name}' + (f'  -- {detail}' if detail else ''))


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def u64(b, o):
    return struct.unpack_from('<Q', b, o)[0]


def be32(b, o):
    return struct.unpack_from('>I', b, o)[0]


def align(n, p):
    return (n + p - 1) // p * p


def cstr(b):
    return b.split(b'\0')[0].decode('ascii', 'replace')


def fdt_props(blob):
    if len(blob) < 40 or blob[:4] != FDT_MAGIC:
        return None
    os_, ostr = be32(blob, 8), be32(blob, 12)
    p = os_
    if p + 4 > len(blob) or be32(blob, p) != 1:
        return None
    p += 4
    while p < len(blob) and blob[p] != 0:
        p += 1
    p = (p + 4) & ~3
    props = {}
    while p + 4 <= len(blob):
        t = be32(blob, p); p += 4
        if t in (1, 2, 9):
            break
        if t == 4:
            continue
        if t == 3:
            ln, no = struct.unpack_from('>II', blob, p); p += 8
            v = blob[p:p + ln]; p = (p + ln + 3) & ~3
            e = blob.find(b'\0', ostr + no)
            props[blob[ostr + no:e].decode('ascii', 'replace')] = v
    return props


def keys_of(blob):
    p = fdt_props(blob)
    if not p:
        return None
    out = {}
    for k in ('qcom,msm-id', 'qcom,board-id', 'qcom,pmic-id'):
        v = p.get(k)
        if v and len(v) % 4 == 0:
            out[k] = list(struct.unpack(f'>{len(v)//4}I', v))
    return out


def match_keys(k):
    """ABL scores on msm-id (required) + board-id (required for exact match)."""
    if not k:
        return False, 'no DT keys'
    mi = k.get('qcom,msm-id')
    bi = k.get('qcom,board-id')
    if not mi or mi[:2] != DEVICE['msm-id']:
        return False, f'msm-id {mi} != {DEVICE["msm-id"]}'
    if not bi or bi[:2] != DEVICE['board-id']:
        return False, f'board-id {bi} != {DEVICE["board-id"]}'
    return True, f'msm-id {mi[:2]} board-id {bi[:2]} pmic-id {k.get("qcom,pmic-id")}'


def check_boot(path, part='boot'):
    data = open(path, 'rb').read()
    print(f'\n=== boot image: {path} ===')
    if data[:8] != b'ANDROID!':
        chk(ERR, 'boot magic', f'{data[:8]!r} != ANDROID!')
        return None
    chk(OK, 'boot magic', 'ANDROID!')
    ver = u32(data, 0x28)
    chk(OK if ver in (0, 1, 2, 3, 4) else ERR, 'header_version', str(ver))
    if ver >= 3:
        ps = 4096
        ksz, rsz = u32(data, 8), u32(data, 12)
        hs = u32(data, 0x14)
        chk(OK if hs >= 1580 else ERR, 'header_size >= 1580', str(hs))
        hdr_end = align(max(hs, 1580), ps)
        secs = [('kernel', hdr_end, ksz)]
        off = hdr_end + align(ksz, ps)
        secs.append(('ramdisk', off, rsz))
        dtb = None
    else:
        ps = u32(data, 0x24)
        chk(OK if ps in (2048, 4096, 8192, 16384, 65536) else ERR, 'page_size', hex(ps))
        ksz, rsz = u32(data, 8), u32(data, 0x10)
        hdr_end = align(u32(data, 0x66c), ps) if ver >= 1 else align(1660, ps)
        secs = [('kernel', hdr_end, ksz)]
        off = hdr_end + align(ksz, ps)
        secs.append(('ramdisk', off, rsz))
        off += align(rsz, ps)
        secs.append(('second', off, u32(data, 0x18)))
        off += align(u32(data, 0x18), ps)
        if ver >= 1 and u32(data, 0x660):
            secs.append(('recovery_dtbo', off, u32(data, 0x660)))
            off += align(u32(data, 0x660), ps)
        dtb = None
        if ver >= 2 and u32(data, 0x670):
            dsz, daddr = u32(data, 0x670), u64(data, 0x674)
            secs.append(('dtb', off, dsz))
            dtb = (off, dsz, daddr)
            off += align(dsz, ps)

    for name, o, s in secs:
        end = o + s
        if s == 0:
            chk(WARN, f'{name} size', '0 (empty)') if name in ('kernel',) else None
            continue
        if end > len(data):
            chk(ERR, f'{name} within file', f'off=0x{o:x} size={s} end=0x{end:x} > file 0x{len(data):x}')
        else:
            chk(OK, f'{name} within file', f'off=0x{o:x} size={s}')
    if off > PART[part]:
        chk(ERR, f'fits {part} partition', f'0x{off:x} > 0x{PART[part]:x}')
    else:
        chk(OK, f'fits {part} partition', f'0x{off:x} <= 0x{PART[part]:x}')

    # kernel payload
    if ksz and hdr_end + ksz <= len(data):
        k = data[hdr_end:hdr_end + ksz]
        if k[:2] == b'\x1f\x8b':
            chk(OK, 'kernel payload', 'GZIP (ABL will inflate)')
        elif k[0x38:0x3c] == b'ARMd':
            chk(OK, 'kernel payload', f'raw ARM64 Image, image_size=0x{u64(k,16):x}')
            if u64(k, 16) > PART[part]:
                chk(ERR, 'Image.image_size sane', hex(u64(k, 16)))
        else:
            chk(ERR, 'kernel payload', f'neither gzip nor ARM64 Image (0x38={k[0x38:0x3c].hex()})')

    if dtb:
        o, s, daddr = dtb
        blob = data[o:o + s]
        if blob[:4] != FDT_MAGIC:
            chk(ERR, 'appended DTB magic', blob[:4].hex())
        else:
            tot = be32(blob, 4)
            chk(OK if tot <= s else ERR, 'DTB totalsize <= dtb_size', f'{tot} vs {s}')
            ok, why = match_keys(keys_of(blob))
            chk(OK if ok else ERR, 'DTB matches this device', why)
            chk(OK, 'DTB load address', hex(daddr))
    elif ver < 3:
        chk(ERR, 'appended DTB present', 'header v2 with no dtb section -> ABL aborts')

    if ver < 3:
        chk(WARN, 'header v2 on an A14/v4-oriented ABL',
            'supported in code, but v2 leaves vendor_boot/recovery image_info fields unset')
    return {'ver': ver, 'dtb': dtb}


def check_init_boot(path):
    data = open(path, 'rb').read()
    print(f'\n=== init_boot: {path} ===')
    if data[:8] != b'ANDROID!':
        chk(ERR, 'magic', repr(data[:8])); return
    chk(OK, 'magic', 'ANDROID!')
    ver = u32(data, 0x28)
    chk(OK if ver == 4 else ERR, 'header_version (must be 4)', str(ver))
    rsz = u32(data, 12)
    chk(OK if rsz else ERR, 'ramdisk_size', str(rsz))
    end = 4096 + align(rsz, 4096)
    chk(OK if end <= PART['init_boot'] else ERR, 'fits init_boot partition',
        f'0x{end:x} <= 0x{PART["init_boot"]:x}')
    if rsz and 4096 + rsz <= len(data):
        blob = data[4096:4096 + rsz]
        magic = blob[:6]
        kind = ('gzip' if magic[:2] == b'\x1f\x8b' else
                'cpio(newc)' if blob[:6] == b'070701' else
                'lz4' if blob[:4] == b'\x04\x22\x4d\x18' else 'unknown')
        chk(OK if kind != 'unknown' else WARN, 'ramdisk format', kind)


def check_vendor_boot(path):
    data = open(path, 'rb').read()
    print(f'\n=== vendor_boot: {path} ===')
    if data[:8] != b'VNDRBOOT':
        chk(ERR, 'magic', repr(data[:8])); return
    chk(OK, 'magic', 'VNDRBOOT')
    ver = u32(data, 8)
    chk(OK if ver == 4 else ERR, 'header_version (must be 4)', str(ver))
    ps = u32(data, 0xc)
    vrs = u32(data, 0x18)
    hs = u32(data, 0x830)
    dsz = u32(data, 0x834)
    daddr = u64(data, 0x838)
    tsz = u32(data, 0x840) if ver >= 4 else 0
    bcs = u32(data, 0x84c) if ver >= 4 else 0
    cmd = cstr(data[0x1c:0x81c])
    chk(OK, 'cmdline', repr(cmd))
    chk(OK if dsz else ERR, 'dtb_size', str(dsz))
    off = align(max(hs, 0x840), ps) + align(vrs, ps)
    if tsz:
        off += align(tsz, ps)
    doff = off
    if dsz and doff + dsz <= len(data):
        blob = data[doff:doff + dsz]
        n, pos, found = 0, 0, False
        while True:
            i = blob.find(FDT_MAGIC, pos)
            if i < 0:
                break
            # real FDT? totalsize sane + version 17 + last_comp_version 16
            ok_hdr = False
            if i + 28 <= len(blob):
                tot = be32(blob, i + 4)
                ver_fdt = be32(blob, i + 20)
                lcv = be32(blob, i + 24)
                ok_hdr = (40 <= tot and i + tot <= len(blob)
                          and ver_fdt == 17 and lcv == 16)
            if not ok_hdr:
                pos = i + 4          # false positive, keep scanning
                continue
            n += 1
            ok, why = match_keys(keys_of(blob[i:i + tot]))
            tag = 'MATCH' if ok else 'no'
            print(f'        FDT #{n} @0x{i:x} totalsize=0x{tot:x}  [{tag}] {why}')
            if ok:
                found = True
            pos = i + tot            # advance past this blob
        chk(OK if found else ERR, 'a DTB in the table matches this device',
            f'{n} valid FDT(s) scanned')
    else:
        chk(ERR, 'dtb section in file', f'off=0x{doff:x} size={dsz}')
    if bcs:
        b = doff + align(dsz, ps)
        if b + bcs <= len(data):
            print('        bootconfig: ' + data[b:b + bcs].decode('ascii', 'replace').replace('\n', ' | '))
    total = doff + align(dsz, ps) + align(bcs, ps)
    chk(OK if total <= PART['vendor_boot'] else ERR, 'fits vendor_boot partition',
        f'0x{total:x} <= 0x{PART["vendor_boot"]:x}')


def check_dtbo(path):
    data = open(path, 'rb').read()
    print(f'\n=== dtbo: {path} ===')
    magic, total, hdrsz, eoff, cnt, esz = struct.unpack_from('>6I', data, 0)
    if magic != DTBO_MAGIC:
        chk(ERR, 'dtbo container magic', hex(magic)); return
    chk(OK, 'dtbo container magic', '0xd7b7ab1e')
    chk(OK if total <= len(data) and total >= hdrsz else ERR, 'total size sane',
        f'total=0x{total:x} file=0x{len(data):x}')
    chk(OK, 'entries', f'count={cnt} entry_size=0x{esz:x} hdrsz=0x{hdrsz:x}')
    hit = []
    for n in range(cnt):
        b = eoff + n * esz
        if b + esz > len(data):
            break
        s, o, mid, bid, pmic = struct.unpack_from('>5I', data, b)
        if o + s > len(data):
            continue
        ok, why = match_keys(keys_of(data[o:o + s]))
        if ok:
            props = fdt_props(data[o:o + s]) or {}
            model = props.get('model', b'?').split(b'\0')[0].decode('ascii', 'replace')
            hit.append((n, model, why))
    if hit:
        chk(WARN, f'{len(hit)} overlay(s) will be applied to YOUR dtb',
            '; '.join(f'#{n} {m}' for n, m, _ in hit[:6]))
        chk(WARN, 'recommendation', 'flash a valid 0-entry dtbo container to B unless you want these overlays')
    else:
        chk(OK, 'no overlay matches this device', 'dtbo is inert')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--boot')
    ap.add_argument('--init-boot')
    ap.add_argument('--vendor-boot')
    ap.add_argument('--dtbo')
    a = ap.parse_args()
    print('TB331FC / khaje ABL conformance check')
    print(f'device keys: msm-id={[hex(x) for x in DEVICE["msm-id"]]} '
          f'board-id={[hex(x) for x in DEVICE["board-id"]]}')
    if a.boot:
        check_boot(a.boot)
    if a.init_boot:
        check_init_boot(a.init_boot)
    if a.vendor_boot:
        check_vendor_boot(a.vendor_boot)
    if a.dtbo:
        check_dtbo(a.dtbo)
    nf = sum(1 for l, _, _ in results if l == ERR)
    nw = sum(1 for l, _, _ in results if l == WARN)
    print(f'\n--- {len(results)} checks: {len(results)-nf-nw} pass, {nw} warn, {nf} FAIL ---')
    return 1 if nf else 0


if __name__ == '__main__':
    sys.exit(main())

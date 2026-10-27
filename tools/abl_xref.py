#!/usr/bin/env python3
"""AArch64 xref resolver for Qualcomm ABL (LinuxLoader.efi).

RVA == file offset for this PE (ImageBase 0, sections 1:1).  Resolves
ADRP+ADD and ADRP+LDR literal loads to absolute addresses and maps them back
to the string table, so we can find which function references which message.
"""
import struct, sys, re

PATH = r'D:\TB331FC_GSI_Kit\LinuxLoader.efi'
TEXT_START = 0x1000
TEXT_END = 0xc0000

ADD_IMM = (0x7f800000, 0x11000000)   # sf | op=0 | S=0 | 100010 | sh=0
LDR_UNS = (0xffc00000, 0xf9400000)   # LDR Xt,[Xn,#imm12*8]
LDR_UNS_W = (0xffc00000, 0xb9400000)


def load(path=PATH):
    return open(path, 'rb').read()


def read_cstr(data, off, maxlen=250):
    if off >= len(data):
        return None
    end = data.find(b'\0', off, off + maxlen)
    if end < 0:
        return None
    raw = data[off:end]
    if len(raw) < 4:
        return None
    try:
        s = raw.decode('ascii')
    except UnicodeDecodeError:
        return None
    if sum(32 <= c < 127 for c in raw) / len(raw) < 0.95:
        return None
    return s


def adrp_page(addr, w):
    immlo = (w >> 29) & 3
    immhi = (w >> 5) & 0x7ffff
    imm = (immhi << 2) | immlo
    if imm & (1 << 20):
        imm -= (1 << 21)
    return ((addr & ~0xfff) + (imm << 12)) & 0xffffffffffff


def scan(data):
    """returns list of (callsite, adrp_at, target_abs)"""
    out = []
    last_adrp = {}
    for addr in range(TEXT_START, TEXT_END, 4):
        w = struct.unpack_from('<I', data, addr)[0]
        if (w & 0x9f000000) == 0x90000000:                 # ADRP
            last_adrp[w & 0x1f] = (addr, adrp_page(addr, w))
            continue
        # ADD (immediate)
        mask, val = ADD_IMM
        if (w & mask) == val:
            rn = (w >> 5) & 0x1f
            if rn in last_adrp:
                pa, page = last_adrp[rn]
                if addr - pa <= 32:
                    imm12 = (w >> 10) & 0xfff
                    sh = (w >> 22) & 1
                    out.append((addr, pa, page + (imm12 << (12 if sh else 0))))
            continue
        # LDR (unsigned offset, 64-bit)
        mask, val = LDR_UNS
        if (w & mask) == val:
            rn = (w >> 5) & 0x1f
            if rn in last_adrp:
                pa, page = last_adrp[rn]
                if addr - pa <= 32:
                    imm12 = (w >> 10) & 0xfff
                    out.append((addr, pa, page + (imm12 << 3)))
            continue
        mask, val = LDR_UNS_W
        if (w & mask) == val:
            rn = (w >> 5) & 0x1f
            if rn in last_adrp:
                pa, page = last_adrp[rn]
                if addr - pa <= 32:
                    imm12 = (w >> 10) & 0xfff
                    out.append((addr, pa, page + (imm12 << 2)))
    return out


def main():
    path = PATH
    pat = None
    args = sys.argv[1:]
    if args and not args[0].startswith('-'):
        pat = args[0]
        args = args[1:]
    for i, a in enumerate(args):
        if a == '-f':
            path = args[i + 1]
    data = load(path)
    pairs = scan(data)
    print(f'# resolved page-relative loads: {len(pairs)}')
    xref = {}
    for callsite, adrp_at, tgt in pairs:
        s = read_cstr(data, tgt)
        if s:
            xref.setdefault(tgt, []).append((callsite, s))
    print(f'# string targets referenced: {len(xref)}')
    rx = re.compile(pat, re.I) if pat else None
    rows = []
    for tgt in sorted(xref):
        s = xref[tgt][0][1]
        if rx and not rx.search(s):
            continue
        calls = ', '.join(f'0x{c:x}' for c, _ in xref[tgt])
        rows.append((calls, tgt, s))
    for calls, tgt, s in rows:
        print(f'  {calls:28s} -> str@0x{tgt:06x}  {s[:130]}')


if __name__ == '__main__':
    main()

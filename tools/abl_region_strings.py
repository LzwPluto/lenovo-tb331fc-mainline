#!/usr/bin/env python3
"""List every string referenced from inside an address range of the ABL.

Gives a quick "what can go wrong here" map for a big function.
"""
import struct, sys

PATH = r'D:\TB331FC_GSI_Kit\LinuxLoader.efi'
STR_LO, STR_HI = 0x96000, 0xb0000


def load():
    return open(PATH, 'rb').read()


def adrp_page(addr, w):
    immlo = (w >> 29) & 3
    immhi = (w >> 5) & 0x7ffff
    imm = (immhi << 2) | immlo
    if imm & (1 << 20):
        imm -= (1 << 21)
    return ((addr & ~0xfff) + (imm << 12)) & 0xffffffffffff


def cstr(d, off, maxlen=220):
    if not (STR_LO <= off < STR_HI):
        return None
    end = d.find(b'\0', off, off + maxlen)
    if end < 0:
        return None
    raw = d[off:end]
    if len(raw) < 5:
        return None
    try:
        s = raw.decode('ascii')
    except UnicodeDecodeError:
        return None
    if sum(32 <= c < 127 for c in raw) / len(raw) < 0.95:
        return None
    return s


def main():
    lo = int(sys.argv[1], 0)
    hi = int(sys.argv[2], 0)
    d = load()
    last = {}
    seen = set()
    out = []
    for a in range(lo, hi, 4):
        w = struct.unpack_from('<I', d, a)[0]
        if (w & 0x9f000000) == 0x90000000:
            last[w & 0x1f] = (a, adrp_page(a, w))
            continue
        if (w & 0x7f800000) == 0x11000000:          # ADD imm
            rn = (w >> 5) & 0x1f
            if rn in last and a - last[rn][0] <= 32:
                pg = last[rn][1]
                imm12 = (w >> 10) & 0xfff
                sh = (w >> 22) & 1
                tgt = pg + (imm12 << (12 if sh else 0))
                s = cstr(d, tgt)
                if s and s not in seen:
                    seen.add(s)
                    out.append((a, s))
    print(f'# {len(out)} distinct strings referenced in 0x{lo:x}..0x{hi:x}')
    for a, s in out:
        print(f'  0x{a:06x}  {s[:150]}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Find every store to a given stack slot inside a function and show context.

This is how you recover "under what condition does this function return error".
"""
import struct, sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

PATH = r'D:\TB331FC_GSI_Kit\LinuxLoader.efi'
MD = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
STR_LO, STR_HI = 0x96000, 0xb0000


def load():
    return open(PATH, 'rb').read()


def adrp_page(a, w):
    immlo = (w >> 29) & 3
    immhi = (w >> 5) & 0x7ffff
    imm = (immhi << 2) | immlo
    if imm & (1 << 20):
        imm -= (1 << 21)
    return ((a & ~0xfff) + (imm << 12)) & 0xffffffffffff


def cstr(d, off, n=200):
    if not (STR_LO <= off < STR_HI):
        return None
    e = d.find(b'\0', off, off + n)
    if e < 0:
        return None
    raw = d[off:e]
    if len(raw) < 5:
        return None
    try:
        s = raw.decode('ascii')
    except UnicodeDecodeError:
        return None
    if sum(32 <= c < 127 for c in raw) / len(raw) < 0.95:
        return None
    return s


def annotate(d, a, w, last):
    """string reference for the current insn, if any"""
    if (w & 0x9f000000) == 0x90000000:
        last[w & 0x1f] = (a, adrp_page(a, w))
        return ''
    if (w & 0x7f800000) == 0x11000000:
        rn = (w >> 5) & 0x1f
        if rn in last and a - last[rn][0] <= 32:
            pg = last[rn][1]
            imm12 = (w >> 10) & 0xfff
            sh = (w >> 22) & 1
            s = cstr(d, pg + (imm12 << (12 if sh else 0)))
            if s:
                return f'    ; "{s[:110]}"'
    return ''


def main():
    lo = int(sys.argv[1], 0)
    hi = int(sys.argv[2], 0)
    slot = int(sys.argv[3], 0)
    ctx = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    d = load()
    stores = []
    for a in range(lo, hi, 4):
        w = struct.unpack_from('<I', d, a)[0]
        # STRB (imm): 0x39000000 ; STR (imm): 0xb9000000 ; both with Rn=31 (sp)
        for mask, val in ((0xffc00000, 0x39000000), (0xffc00000, 0xb9000000)):
            if (w & mask) == val:
                imm = (w >> 10) & 0xfff
                scale = 1 if val == 0x39000000 else 4
                if imm * scale == slot and ((w >> 5) & 0x1f) == 31:
                    stores.append(a)
                break
    print(f'# stores to [sp, #0x{slot:x}] inside 0x{lo:x}..0x{hi:x}: {len(stores)}')
    for s in stores:
        print(f'\n=== store at 0x{s:x} ===')
        last = {}
        start = max(lo, s - ctx * 4)
        for a in range(start, s + 4, 4):
            w = struct.unpack_from('<I', d, a)[0]
            note = annotate(d, a, w, last)
            for ins in MD.disasm(d[a:a + 4], a):
                mark = ' <== STORE' if a == s else ''
                print(f'  0x{a:06x}  {ins.mnemonic:<7s} {ins.op_str}{note}{mark}')
                break


if __name__ == '__main__':
    main()

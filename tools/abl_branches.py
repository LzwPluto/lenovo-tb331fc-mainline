#!/usr/bin/env python3
"""Print every conditional branch in an address range, with the instructions
that set up the condition.  This is the fastest way to read a big function's
decision logic without drowning in debug-print boilerplate.
"""
import struct, sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

PATH = r'D:\TB331FC_GSI_Kit\LinuxLoader.efi'
MD = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
STR_LO, STR_HI = 0x96000, 0xb0000
COND = ('cbz', 'cbnz', 'tbz', 'tbnz')


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


def main():
    lo, hi = int(sys.argv[1], 0), int(sys.argv[2], 0)
    before = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    d = load()
    last = {}
    lines = {}
    for a in range(lo, hi, 4):
        w = struct.unpack_from('<I', d, a)[0]
        note = ''
        if (w & 0x9f000000) == 0x90000000:
            last[w & 0x1f] = (a, adrp_page(a, w))
        elif (w & 0x7f800000) == 0x11000000:
            rn = (w >> 5) & 0x1f
            if rn in last and a - last[rn][0] <= 32:
                pg = last[rn][1]
                imm12 = (w >> 10) & 0xfff
                sh = (w >> 22) & 1
                s = cstr(d, pg + (imm12 << (12 if sh else 0)))
                if s:
                    note = f'   ; "{s[:100]}"'
        for ins in MD.disasm(d[a:a + 4], a):
            lines[a] = (ins.mnemonic, ins.op_str, note)
            break
        else:
            lines[a] = ('.word', f'0x{w:08x}', '')

    addrs = sorted(lines)
    for a in addrs:
        mn, ops, note = lines[a]
        if mn in COND or (mn.startswith('b.') and mn != 'b.eq' or False) or mn.startswith('b.'):
            if not (mn in COND or mn.startswith('b.')):
                continue
            i = addrs.index(a)
            print(f'\n=== branch 0x{a:x}  {mn} {ops} ===')
            for j in range(max(0, i - before), i + 1):
                aa = addrs[j]
                m2, o2, n2 = lines[aa]
                mark = '  <<<' if aa == a else ''
                print(f'  0x{aa:06x}  {m2:<7s} {o2}{n2}{mark}')


if __name__ == '__main__':
    main()

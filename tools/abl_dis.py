#!/usr/bin/env python3
"""Linear disassembler for the ABL .text with resolved string/PC-relative hints."""
import struct, sys, re
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

PATH = r'D:\TB331FC_GSI_Kit\LinuxLoader.efi'
STR_LO, STR_HI = 0x96000, 0xb0000

MD = Cs(CS_ARCH_ARM64, CS_MODE_ARM)


def load(path=PATH):
    return open(path, 'rb').read()


def read_cstr(data, off, maxlen=250):
    if not (STR_LO <= off < STR_HI):
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


def disasm(start, end, path=PATH, annotate=True):
    data = load(path)
    last_adrp = {}
    out = []
    for addr in range(start, end, 4):
        w = struct.unpack_from('<I', data, addr)[0]
        note = ''
        if (w & 0x9f000000) == 0x90000000:
            last_adrp[w & 0x1f] = (addr, adrp_page(addr, w))
        elif (w & 0x7f800000) == 0x11000000:      # ADD imm
            rn = (w >> 5) & 0x1f
            if rn in last_adrp and addr - last_adrp[rn][0] <= 32:
                pa, page = last_adrp[rn]
                imm12 = (w >> 10) & 0xfff
                sh = (w >> 22) & 1
                tgt = page + (imm12 << (12 if sh else 0))
                s = read_cstr(data, tgt)
                if s:
                    note = f'   ; "{s[:110]}"'
                elif STR_LO <= tgt < STR_HI:
                    note = f'   ; data@0x{tgt:x}'
        for ins in MD.disasm(data[addr:addr + 4], addr):
            out.append(f'  {addr:06x}:  {ins.mnemonic:<8s} {ins.op_str}{note}')
            break
        else:
            out.append(f'  {addr:06x}:  .word 0x{w:08x}')
    return '\n'.join(out)


if __name__ == '__main__':
    a = int(sys.argv[1], 0)
    b = int(sys.argv[2], 0)
    p = PATH
    if len(sys.argv) > 3:
        p = sys.argv[3]
    print(f'; disasm 0x{a:x}..0x{b:x} of {p}')
    print(disasm(a, b, p))

#!/usr/bin/env python3
"""For each error-exit address, find the error message printed just before it.

Error exits look like:
    ... bl #0x1304 (the print)          <- message string set up earlier
    mov x8, #CODE ; movk x8, #0x8000, lsl #48
    str x8, [sp, #STATUS]
    b   #EPILOGUE
so we walk backwards to the most recent "adrp+add <string>" pair.
"""
import struct, sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

PATH = r'D:\TB331FC_GSI_Kit\LinuxLoader.efi'
MD = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
STR_LO, STR_HI = 0x96000, 0xb0000

EFI = {1: 'EFI_LOAD_ERROR', 2: 'EFI_INVALID_PARAMETER', 3: 'EFI_UNSUPPORTED',
       4: 'EFI_BAD_BUFFER_SIZE', 5: 'EFI_BUFFER_TOO_SMALL', 6: 'EFI_NOT_READY',
       7: 'EFI_DEVICE_ERROR', 8: 'EFI_WRITE_PROTECTED', 9: 'EFI_OUT_OF_RESOURCES',
       10: 'EFI_VOLUME_CORRUPTED', 11: 'EFI_VOLUME_FULL', 12: 'EFI_NO_MEDIA',
       13: 'EFI_MEDIA_CHANGED', 14: 'EFI_NOT_FOUND', 15: 'EFI_ACCESS_DENIED'}


def load():
    return open(PATH, 'rb').read()


def adrp_page(a, w):
    immlo = (w >> 29) & 3
    immhi = (w >> 5) & 0x7ffff
    imm = (immhi << 2) | immlo
    if imm & (1 << 20):
        imm -= (1 << 21)
    return ((a & ~0xfff) + (imm << 12)) & 0xffffffffffff


def cstr(d, off, n=220):
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
    d = load()

    # build string reference map for the whole range
    last = {}
    strref = {}
    for a in range(lo - 0x400, hi, 4):
        w = struct.unpack_from('<I', d, a)[0]
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
                    strref[a] = s

    ref_addrs = sorted(strref)
    print(f'# string refs in window: {len(ref_addrs)}')

    # find error exits
    for a in range(lo, hi, 4):
        w = struct.unpack_from('<I', d, a)[0]
        if (w & 0xffc00000) != 0xf9000000:
            continue
        if ((w >> 5) & 0x1f) != 31:
            continue
        # look back for the movk/mov pair that set x8
        code = None
        for b in range(a - 4, max(lo, a - 20), -4):
            wb = struct.unpack_from('<I', d, b)[0]
            if (wb & 0xffe0001f) == 0xf2a00008 or (wb & 0xffe0001f) == 0xf2a00009:
                pass
            ins = list(MD.disasm(d[b:b + 4], b))
            if not ins:
                continue
            m, o = ins[0].mnemonic, ins[0].op_str
            if m == 'movk' and 'lsl #48' in o and o.startswith('x8'):
                for c in range(b - 4, max(lo, b - 16), -4):
                    ic = list(MD.disasm(d[c:c + 4], c))
                    if ic and ic[0].mnemonic == 'mov' and ic[0].op_str.startswith('x8, #'):
                        code = int(ic[0].op_str.split('#')[1], 0)
                        break
                break
        if code is None:
            continue
        prev = [x for x in ref_addrs if x < a]
        msg = strref[prev[-1]] if prev and a - prev[-1] < 160 else '(no message)'
        print(f'  0x{a:06x}  code={code:<2d} {EFI.get(code,"?"):<24s} {msg[:110]}')


if __name__ == '__main__':
    main()

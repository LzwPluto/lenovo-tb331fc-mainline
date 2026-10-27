#!/usr/bin/env python3
"""Show every epilogue (ret) in a function, with the instructions leading up to it.

The tail of each epilogue shows what value is being returned, which tells us
which failure paths are fatal and which merely warn.
"""
import struct, sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

PATH = r'D:\TB331FC_GSI_Kit\LinuxLoader.efi'
MD = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
RET = 0xd65f03c0


def load():
    return open(PATH, 'rb').read()


def main():
    lo = int(sys.argv[1], 0)
    hi = int(sys.argv[2], 0)
    ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    d = load()
    rets = [a for a in range(lo, hi, 4)
            if struct.unpack_from('<I', d, a)[0] == RET]
    print(f'# {len(rets)} ret(s) in 0x{lo:x}..0x{hi:x}')
    for r in rets:
        start = max(lo, r - ctx * 4)
        print(f'\n--- epilogue at 0x{r:x} ---')
        for a in range(start, r + 4, 4):
            for ins in MD.disasm(d[a:a + 4], a):
                print(f'  0x{a:06x}  {ins.mnemonic:<7s} {ins.op_str}')
                break


if __name__ == '__main__':
    main()

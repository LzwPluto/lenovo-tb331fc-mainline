#!/usr/bin/env python3
"""inspect_mdt.py - dump an .mdt ELF program header table next to the .bNN sizes"""
import os
import struct
import sys

PT_LOAD = 1

def main(mdt):
    data = open(mdt, 'rb').read()
    base = mdt[:-4] if mdt.lower().endswith('.mdt') else mdt
    e_phoff, = struct.unpack_from('<I', data, 28)
    e_phentsize, e_phnum = struct.unpack_from('<HH', data, 42)
    ei_class = data[4]
    fmt = '<IIIIIIII' if ei_class == 1 else '<IIQQQQQQ'
    print(f'{os.path.basename(mdt)}: ELF{32 if ei_class==1 else 64}, '
          f'{e_phnum} phdrs, phoff=0x{e_phoff:x}')
    print(f'{"idx":>3} {"type":>6} {"filesz":>10} {"memsz":>10} {"paddr":>12}  '
          f'{"segfile":>12} {"actual":>10}')
    # actual segment files
    segs = {}
    for f in os.listdir(os.path.dirname(base) or '.'):
        p = os.path.join(os.path.dirname(base), f)
        if f.startswith(os.path.basename(base) + '.b'):
            segs[f[len(os.path.basename(base)) + 1:]] = os.path.getsize(p)
    for i in range(e_phnum):
        t, off, va, pa, fsz, msz, fl, al = struct.unpack_from(fmt, data, e_phoff + i * e_phentsize)
        name = f'b{i:02d}'
        actual = segs.get(name, segs.get(f'b{i}', None))
        mark = ''
        if t == PT_LOAD and fsz:
            mark = ' <LOAD'
        print(f'{i:>3} {t:>6} {fsz:>10} {msz:>10} {pa:>12x}  {name:>12} '
              f'{actual if actual is not None else "-":>10}{mark}')
    print()
    print('segment files on disk:', dict(sorted(segs.items())))

if __name__ == '__main__':
    main(sys.argv[1])

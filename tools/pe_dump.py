#!/usr/bin/env python3
"""Dump PE info + strings of LinuxLoader.efi / abl_decompressed.bin, filtered."""
import re, sys, os, pefile

def pe_info(path):
    data = open(path, 'rb').read()
    print('=' * 78)
    print(f'FILE {path} size=0x{len(data):x}')
    if data[:2] != b'MZ':
        print('  not MZ; first bytes', data[:16].hex())
        return None
    pe = pefile.PE(data=data, fast_load=True)
    print(f'  Machine=0x{pe.FILE_HEADER.Machine:x}  Subsystem={pe.OPTIONAL_HEADER.Subsystem}  '
          f'ImageBase=0x{pe.OPTIONAL_HEADER.ImageBase:x}  EntryPoint=0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:x}')
    print(f'  SizeOfImage=0x{pe.OPTIONAL_HEADER.SizeOfImage:x}  Sections={pe.FILE_HEADER.NumberOfSections}')
    for s in pe.sections:
        name = s.Name.rstrip(b'\0').decode('latin1')
        print(f'    {name:8s} VA=0x{pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress:09x} '
              f'RVA=0x{s.VirtualAddress:07x} VSize=0x{s.Misc_VirtualSize:08x} '
              f'RawPtr=0x{s.PointerToRawData:08x} RawSize=0x{s.SizeOfRawData:08x}')
    return pe

def strings_of(data, minlen=6):
    out = []
    cur = bytearray()
    start = 0
    for i, b in enumerate(data):
        if 32 <= b < 127 or b in (9,):
            if not cur:
                start = i
            cur.append(b)
        else:
            if len(cur) >= minlen:
                out.append((start, cur.decode('ascii')))
            cur = bytearray()
    if len(cur) >= minlen:
        out.append((start, cur.decode('ascii')))
    return out

KEY = re.compile(r'(?i)(dtb|device tree|fdt|gzip|inflate|decompress|retry|slot|avb|verif|'
                 r'memory|reserved|boot error|abort|halt|kernel|ramdisk|vendor_boot|init_boot|'
                 r'pmic|board-id|msm-id|match|failed|error|panic|fastboot|imagefv|dtbo)')

if __name__ == '__main__':
    mode = sys.argv[1]
    path = sys.argv[2]
    if mode in ('pe', 'all'):
        pe_info(path)
    data = open(path, 'rb').read()
    ss = strings_of(data)
    print(f'  total strings={len(ss)}')
    filt = sys.argv[3] if len(sys.argv) > 3 else None
    if filt:
        rx = re.compile(filt, re.I)
        for off, s in ss:
            if rx.search(s):
                print(f'    {off:06x}  {s}')

#!/usr/bin/env python3
"""pil_squasher.py - merge Qualcomm split firmware (.mdt + .bNN) into one .mbn

Why: mainline's qcom_q6v5_pas requests the exact filename in `firmware-name`
(usually `adsp.mbn`) and does NOT fall back to `<name>.mdt`.  The vendor ships
the split form (an ELF whose program headers point at separate `<name>.bNN`
segment files).  Our workaround was `ln -sf adsp.mdt adsp.mbn`, which happens to
work for adsp but fails for cdsp ("error -22 reading firmware metadata").

This produces a real single-file .mbn: the ELF header + program headers are kept
verbatim, every PT_LOAD segment from `<name>.bNN` is appended, and each program
header's p_offset is rewritten to point into the merged file.

Usage:
    python3 pil_squasher.py adsp.mdt adsp.mbn
    python3 pil_squasher.py /path/to/cdsp.mdt     # output defaults to cdsp.mbn
"""
import os
import struct
import sys

PT_LOAD = 1
ALIGN = 0x1000


def align_up(v, a):
    return (v + a - 1) // a * a


def parse_elf(data):
    if data[:4] != b'\x7fELF':
        raise ValueError('not an ELF file')
    ei_class = data[4]          # 1 = 32-bit, 2 = 64-bit
    ei_data = data[5]           # 1 = little endian
    if ei_data != 1:
        raise ValueError('only little-endian supported')
    if ei_class == 1:
        e_phoff, = struct.unpack_from('<I', data, 28)
        e_phentsize, e_phnum = struct.unpack_from('<HH', data, 42)
        fmt = '<IIIIIIII'        # type, offset, vaddr, paddr, filesz, memsz, flags, align
    elif ei_class == 2:
        e_phoff, = struct.unpack_from('<Q', data, 32)
        e_phentsize, e_phnum = struct.unpack_from('<HH', data, 54)
        fmt = '<IIQQQQQQ'
    else:
        raise ValueError('bad EI_CLASS')
    phdrs = []
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        vals = list(struct.unpack_from(fmt, data, off))
        phdrs.append({'index': i, 'off_in_file': off, 'vals': vals})
    return ei_class, e_phoff, e_phentsize, e_phnum, fmt, phdrs


def squash(mdt_path, mbn_path):
    base = mdt_path[:-4] if mdt_path.lower().endswith('.mdt') else mdt_path
    data = bytearray(open(mdt_path, 'rb').read())
    ei_class, e_phoff, e_phentsize, e_phnum, fmt, phdrs = parse_elf(data)

    print(f'{os.path.basename(mdt_path)}: ELF{32 if ei_class == 1 else 64}, '
          f'{e_phnum} program headers, {len(data)} bytes')

    # Qualcomm split firmware: the segment file index IS the program header
    # index, i.e. phdr[i] <-> "<base>.b<i:02x>".  Verified against the real
    # images: phdr[2].filesz == size(cdsp.b02), phdr[5] == size(cdsp.b05), ...
    # phdr[0]/[1] are PT_NULL but still carry data (hash/metadata), so we take
    # every entry with filesz > 0 regardless of p_type.
    segments = []           # (phdr, payload, new_offset)

    header_end = e_phoff + e_phnum * e_phentsize
    cursor = align_up(header_end, ALIGN)

    for ph in phdrs:
        p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = ph['vals']
        if p_filesz == 0:
            continue
        i = ph['index']
        seg_file = f'{base}.b{i:02d}'
        if not os.path.exists(seg_file):
            alt = f'{base}.b{i}'
            if os.path.exists(alt):
                seg_file = alt
            else:
                print(f'  WARN phdr[{i}] has filesz=0x{p_filesz:x} but no {seg_file} - skipped')
                continue
        payload = open(seg_file, 'rb').read()
        if len(payload) != p_filesz:
            print(f'  WARN {os.path.basename(seg_file)}: {len(payload)} bytes vs '
                  f'filesz 0x{p_filesz:x} - using the shorter length')
            p_filesz = min(len(payload), p_filesz)
            payload = payload[:p_filesz]

        new_off = align_up(cursor, ALIGN)
        segments.append((ph, payload, new_off))
        print(f'  phdr[{i:>2}] type={p_type} {os.path.basename(seg_file):10s} '
              f'filesz=0x{p_filesz:<8x} paddr=0x{p_paddr:<10x} -> offset 0x{new_off:x}')
        cursor = new_off + p_filesz

    # rewrite p_offset for each segment in the phdr table
    for ph, payload, new_off in segments:
        vals = ph['vals']
        if ei_class == 1:
            struct.pack_into('<I', data, ph['off_in_file'] + 4, new_off)
        else:
            struct.pack_into('<Q', data, ph['off_in_file'] + 8, new_off)

    # assemble: header+phdrs, then segments at their offsets
    out = bytearray(data[:header_end])
    for ph, payload, new_off in segments:
        if len(out) < new_off:
            out += b'\x00' * (new_off - len(out))
        out[new_off:new_off + len(payload)] = payload
        if len(out) < new_off + len(payload):
            out += b'\x00' * (new_off + len(payload) - len(out))

    open(mbn_path, 'wb').write(bytes(out))
    print(f'  -> {mbn_path}: {len(out)} bytes, {len(segments)} segments merged')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    mdt = sys.argv[1]
    mbn = sys.argv[2] if len(sys.argv) > 2 else (
        mdt[:-4] + '.mbn' if mdt.lower().endswith('.mdt') else mdt + '.mbn')
    squash(mdt, mbn)

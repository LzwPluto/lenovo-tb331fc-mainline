#!/usr/bin/env python3
"""mkv2.py - build an Android boot image header v2 (packed layout) from parts.

Layout (packed, sizeof = 1660):
  0x000 magic[8]            0x008 kernel_size   0x00c kernel_addr
  0x010 ramdisk_size        0x014 ramdisk_addr  0x018 second_size
  0x01c second_addr         0x020 tags_addr     0x024 page_size
  0x028 header_version      0x02c os_version    0x030 name[16]
  0x040 cmdline[512]        0x240 id[8]         0x260 extra_cmdline[1024]
  0x660 recovery_dtbo_size  0x664 recovery_dtbo_offset(u64)
  0x66c header_size         0x670 dtb_size      0x674 dtb_addr(u64)

Sections start page-aligned: kernel, ramdisk, second, [recovery_dtbo], [dtb]
"""
import argparse, struct, os

PAGE = 4096
HDR_SIZE = 1660


def align(n, p=PAGE):
    return (n + p - 1) // p * p


def build(kernel, ramdisk, dtb, cmdline, out,
          kernel_addr=0x00008000, ramdisk_addr=0x01000000,
          tags_addr=0x00000100, dtb_addr=0x01F00000, os_version=0x200001a9):
    k = open(kernel, 'rb').read() if kernel else b''
    r = open(ramdisk, 'rb').read() if ramdisk else b''
    d = open(dtb, 'rb').read() if dtb else b''
    cb = cmdline.encode()[:511]

    hdr = bytearray(HDR_SIZE)
    hdr[0:8] = b'ANDROID!'
    struct.pack_into('<I', hdr, 0x008, len(k))
    struct.pack_into('<I', hdr, 0x00c, kernel_addr)
    struct.pack_into('<I', hdr, 0x010, len(r))
    struct.pack_into('<I', hdr, 0x014, ramdisk_addr)
    struct.pack_into('<I', hdr, 0x018, 0)                 # second_size
    struct.pack_into('<I', hdr, 0x01c, 0)                 # second_addr
    struct.pack_into('<I', hdr, 0x020, tags_addr)
    struct.pack_into('<I', hdr, 0x024, PAGE)
    struct.pack_into('<I', hdr, 0x028, 2)                 # header_version = 2
    struct.pack_into('<I', hdr, 0x02c, os_version)
    hdr[0x040:0x040 + len(cb)] = cb
    struct.pack_into('<I', hdr, 0x660, 0)                 # recovery_dtbo_size
    struct.pack_into('<Q', hdr, 0x664, 0)                 # recovery_dtbo_offset
    struct.pack_into('<I', hdr, 0x66c, HDR_SIZE)          # header_size
    struct.pack_into('<I', hdr, 0x670, len(d))            # dtb_size
    struct.pack_into('<Q', hdr, 0x674, dtb_addr)          # dtb_addr

    buf = bytearray()
    buf += hdr
    buf += b'\0' * (align(HDR_SIZE) - len(buf))
    off_k = len(buf)
    buf += k
    buf += b'\0' * (align(len(buf)) - len(buf))
    off_r = len(buf)
    buf += r
    buf += b'\0' * (align(len(buf)) - len(buf))
    off_d = len(buf)
    buf += d
    buf += b'\0' * (align(len(buf)) - len(buf))

    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    open(out, 'wb').write(bytes(buf))
    is_gz = (k[:2] == b'\x1f\x8b')
    print(f'{out}')
    print(f'  kernel  off=0x{off_k:x} size={len(k)}  gzip={"yes" if is_gz else "no"}')
    print(f'  ramdisk off=0x{off_r:x} size={len(r)}')
    print(f'  dtb     off=0x{off_d:x} size={len(d)}')
    print(f'  file    size={len(buf)} (0x{len(buf):x})')
    # collision report
    if r and d:
        rs, re_ = ramdisk_addr, ramdisk_addr + len(r)
        ds, de = dtb_addr, dtb_addr + len(d)
        if ds < re_ and rs < de:
            print(f'  !! RAMDISK/DTB LOAD OVERLAP: ramdisk 0x{rs:x}..0x{re_:x} vs dtb 0x{ds:x}..0x{de:x}')
        else:
            print(f'  load ranges OK: ramdisk 0x{rs:x}..0x{re_:x} / dtb 0x{ds:x}..0x{de:x}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--kernel', default='')
    ap.add_argument('--ramdisk', default='')
    ap.add_argument('--dtb', default='')
    ap.add_argument('--cmdline', default='')
    ap.add_argument('--out', required=True)
    ap.add_argument('--dtb-addr', type=lambda s: int(s, 0), default=0x01F00000)
    a = ap.parse_args()
    build(a.kernel, a.ramdisk, a.dtb, a.cmdline, a.out, dtb_addr=a.dtb_addr)

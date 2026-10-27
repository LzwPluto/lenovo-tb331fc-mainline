#!/usr/bin/env python3
"""Function boundary + caller finder for the ABL .text.

Uses a prologue heuristic ("sub sp, sp, #imm" preceded by a terminator) and
scans for BL instructions that target the recovered function start.
"""
import struct, sys

PATH = r'D:\TB331FC_GSI_Kit\LinuxLoader.efi'
TEXT_START, TEXT_END = 0x1000, 0xc0000


def load():
    return open(PATH, 'rb').read()


def insn(d, a):
    return struct.unpack_from('<I', d, a)[0]


def is_bl(w):
    return (w & 0xfc000000) == 0x94000000


def bl_target(a, w):
    imm = w & 0x3ffffff
    if imm & (1 << 25):
        imm -= (1 << 26)
    return (a + (imm << 2)) & 0xffffffffffffffff


def is_prologue(w):
    # sub sp, sp, #imm  ->  0xd10xxxxx family (SUB imm, 64-bit, Rd=SP, Rn=SP)
    # encoding: sf=1 op=1 S=0 100010 sh imm12 Rn=31 Rd=31
    return (w & 0xffc003ff) == 0xd10003ff or (w & 0xff8003ff) == 0xd10003ff


def find_func_start(d, addr):
    a = addr
    while a > TEXT_START:
        w = insn(d, a)
        if is_prologue(w):
            # make sure the previous insn is a terminator (ret / udf / b)
            pw = insn(d, a - 4)
            if pw == 0xd65f03c0 or (pw & 0xffff0000) == 0x00000000 or pw == 0x00000000:
                return a
            if (pw & 0xffe0001f) == 0xd65f0000:   # ret variants
                return a
        a -= 4
    return TEXT_START


def callers_of(d, target):
    out = []
    for a in range(TEXT_START, TEXT_END, 4):
        w = insn(d, a)
        if is_bl(w) and bl_target(a, w) == target:
            out.append(a)
    return out


if __name__ == '__main__':
    d = load()
    for arg in sys.argv[1:]:
        addr = int(arg, 0)
        fs = find_func_start(d, addr)
        print(f'address 0x{addr:x} -> function start 0x{fs:x}')
        cs = callers_of(d, fs)
        print(f'  callers: {[hex(c) for c in cs] if cs else "(none - might be reached via a function pointer)"}')

#!/usr/bin/env python3
"""analyze_nvt_workfunc.py

Turn the raw objdump listing of nvt36523_spi.ko into an annotated control-flow
listing for one function, so the vendor logic can actually be read:

  * resolves bl targets to symbol names
  * tracks `mov wN, #imm` / `movz` so `cmp wN, #imm` can be labelled
  * marks backward branches (loops) and their targets
  * flags every memory write (strb/str) and every sleep/udelay call

Usage: analyze_nvt_workfunc.py <dis-file> <start-sym-substr>
"""
import re
import sys

# constant helpers used by the driver
KNOWN_IMM = {
    0xfe: '0xFE (special event?)',
    0xff: '0xFF (release / no-data)',
    0xfd: '0xFD (WDT)',
    0x77: '0x77 (idle)',
    0xaa: '0xAA (sw_reset_idle)',
    0x55: '0x55 (sw_reset)',
    0x69: '0x69 (bootloader_reset)',
    0x69 + 0x100: '',
    0x6d: '0x6D (109 byte packet)',
    0xa5: '0xA5',
    0x01: '1',
}

CALL_NOTE = {
    'msleep': 'SLEEP',
    'mdelay': 'DELAY',
    'udelay': 'DELAY',
    'nvt_update_firmware': '*** FIRMWARE RELOAD ***',
    'nvt_restore_cmd_func': '*** resend scan cmds ***',
    'nvt_write_addr': 'WRITE-REG',
    'CTP_SPI_WRITE': 'SPI-WRITE',
    'CTP_SPI_READ': 'SPI-READ',
    'input_sync': 'report',
    'input_event': 'report',
    'queue_work_on': 'REQUEUE',
    'nvt_sw_reset_idle': 'reset->idle',
    'nvt_bootloader_reset': 'bootloader reset',
    'nvt_read_fw_history': 'read fw history',
}


def load(path, start):
    lines = open(path, encoding='utf-8', errors='replace').read().split('\n')
    out = []
    inside = False
    for ln in lines:
        m = re.match(r'^([0-9a-f]+) <(.+)>:', ln)
        if m and start in m.group(2) and '.cfi_jt' not in m.group(2):
            inside = True
            out.append((int(m.group(1), 16), '', f'===== {m.group(2)} ====='))
            continue
        if m and inside:
            break
        if inside and ln.strip():
            im = re.match(r'\s*([0-9a-f]+):\s+(\S+)\s*(.*)', ln)
            if im:
                out.append((int(im.group(1), 16), im.group(2), im.group(3)))
    return out


def main(path, start):
    ins = load(path, start)
    regs = {}
    for addr, op, args in ins:
        if not op:
            print(args)
            continue

        note = ''
        # track immediates
        m = re.match(r'w(\d+), #(0x[0-9a-f]+|\d+)', args)
        if op in ('mov', 'movz') and m:
            regs[int(m.group(1))] = int(m.group(2), 0)

        # comparisons
        m = re.match(r'w(\d+), #(0x[0-9a-f]+|\d+)', args)
        if op == 'cmp' and m:
            v = int(m.group(2), 0)
            note = f'   <-- compare 0x{v:02X} {KNOWN_IMM.get(v, "")}'

        # calls
        m = re.search(r'bl\s+[0-9a-f]+ <([^>]+)>', f'{op} {args}')
        if op == 'bl':
            m2 = re.search(r'<([^>]+)>', args)
            if m2:
                sym = m2.group(1)
                note = '   ' + CALL_NOTE.get(sym, '')
                if sym in CALL_NOTE:
                    note = '   <<< ' + CALL_NOTE[sym]

        # branches
        if op.startswith('b') and op != 'bl':
            m2 = re.match(r'([0-9a-f]+)\b', args)
            if m2:
                tgt = int(m2.group(1), 16)
                if tgt < addr:
                    note = f'   <-- LOOP back to 0x{tgt:x}'
                else:
                    note = f'   -> 0x{tgt:x}'

        # memory writes
        if op in ('strb', 'str', 'stp') and note == '':
            note = '   [write]'

        print(f'0x{addr:x}: {op:8s} {args}{note}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'nvt_ts_work_func')

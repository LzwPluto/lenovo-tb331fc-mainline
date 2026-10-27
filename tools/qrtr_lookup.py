#!/usr/bin/env python3
"""qrtr_lookup.py - list QMI services published on the QRTR bus

Uses the AF_QIPCRTR socket directly (no libqmi needed):

    socket(AF_QIPCRTR=42, SOCK_DGRAM, 0)
    bind((0, 0))                       -> kernel assigns a port
    sendto(ctrl NEW_LOOKUP, (BCAST, 0))  -> ask the name server
    recv()                               -> NEW_SERVER replies

Why: ath10k_qmi blocks waiting for the WLFW service (id 0x45).  If that service
is absent from the QRTR bus we know the WLAN firmware/subsystem is not running,
which is a completely different fix than "QMI is broken".

Service ids of interest:
    0x45  WLFW   (WLAN firmware / ath10k_qmi)
    0x42  ???
    0x00  (name server itself)
"""
import socket
import struct
import sys
import time

AF_QIPCRTR = 42
QRTR_NODE_BCAST = 0xFFFFFFFF
QRTR_PORT_CTRL = 0

CMD_NEW_LOOKUP = 3
CMD_NEW_SERVER = 4

NAMES = {
    0x00: 'name-server',
    0x45: 'WLFW (WLAN firmware / ath10k_qmi)',
    0x10: 'PDR',
    0x11: 'SysMon',
    0x42: 'PD-Mapper?',
}


def lookup(service=0, instance=0):
    s = socket.socket(AF_QIPCRTR, socket.SOCK_DGRAM)
    s.bind((0, 0))
    s.settimeout(2.0)
    pkt = struct.pack('<I', CMD_NEW_LOOKUP) + struct.pack('<III', service, instance, 0)
    s.sendto(pkt, (QRTR_NODE_BCAST, QRTR_PORT_CTRL))
    found = []
    t0 = time.time()
    while time.time() - t0 < 2.0:
        try:
            data, addr = s.recvfrom(256)
        except socket.timeout:
            break
        if len(data) < 4:
            continue
        cmd = struct.unpack_from('<I', data, 0)[0]
        if cmd == CMD_NEW_SERVER and len(data) >= 20:
            svc, inst, node, port = struct.unpack_from('<IIII', data, 4)
            found.append((svc, inst, node, port))
    s.close()
    return found


def main():
    try:
        print('QRTR bus scan (nodes and services):')
        all_found = []
        for svc in (0, 0x10, 0x11, 0x42, 0x45, 0xffffffff):
            res = lookup(svc)
            for r in res:
                if r not in all_found:
                    all_found.append(r)
        if not all_found:
            print('  (no services answered - the QRTR bus has no peers)')
            return 1
        print(f'  {"service":>8} {"inst":>5} {"node":>6} {"port":>6}   name')
        for svc, inst, node, port in sorted(all_found):
            print(f'  0x{svc:06x} {inst:>5} {node:>6} {port:>6}   '
                  f'{NAMES.get(svc, "")}')
        if any(s == 0x45 for s, *_ in all_found):
            print('\nWLFW present -> ath10k_qmi should be able to connect.')
        else:
            print('\nWLFW (0x45) is NOT on the bus -> no WLAN QMI service.')
            print('That is why ath10k blocks silently: it is waiting for it.')
        return 0
    except OSError as e:
        print(f'socket error: {e} (is CONFIG_QRTR loaded?)')
        return 1


if __name__ == '__main__':
    sys.exit(main())

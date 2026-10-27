#!/usr/bin/env python3
"""add_ipcrtr_channels.py (v2)

QRTR has no transport unless the DT declares a glink channel named "IPCRTR"
under a remote processor's glink-edge node.  Mainline qrtr-smd matches that
property; without it /sys/bus/qrtr stays empty, QMI cannot reach the WLAN
firmware service and ath10k_snoc hangs right after iommu setup.

v2 fix: DTS requires all properties to precede child nodes, so the new child is
appended at the END of the glink-edge body (and any previous insertion is
removed first, making the script idempotent).
"""
import re
import sys

P = '/mnt/d/TB331FCLinux/build/CANONICAL.dts'
t = open(P, encoding='utf-8').read()

NAMES = {1: 'qcom,mpss_qrtr', 2: 'qcom,adsp_qrtr', 3: 'qcom,cdsp_qrtr'}
INTENTS = 'qcom,intents = <0x800 0x05 0x2000 0x03 0x4400 0x02>;'


def strip_existing(text):
    """remove any previously inserted *_qrtr / IPCRTR child node"""
    removed = 0
    while True:
        m = re.search(r'\n(\t+)(qcom,[a-z0-9_]*qrtr) \{', text)
        if not m:
            break
        brace = text.index('{', m.start())
        depth = 0
        k = brace
        while k < len(text):
            if text[k] == '{':
                depth += 1
            elif text[k] == '}':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        end = k + 1
        if text[end:end + 1] == ';':
            end += 1
        text = text[:m.start()] + text[end:]
        removed += 1
    if removed:
        print(f'  removed {removed} previously inserted qrtr node(s)')
    return text


t = strip_existing(t)

added = 0
for m in list(re.finditer(r'\n(\t+)glink-edge \{', t)):
    indent = m.group(1)
    brace = t.index('{', m.start())
    depth = 0
    k = brace
    while k < len(t):
        if t[k] == '{':
            depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    body = t[brace + 1:k]

    pm = re.search(r'qcom,remote-pid = <(0x[0-9a-f]+)>;', body)
    if not pm:
        continue
    if 'IPCRTR' in body:
        continue
    pid = int(pm.group(1), 16)
    name = NAMES.get(pid, f'qcom,rproc{pid}_qrtr')

    inner = indent + '\t'
    insert = (
        f'\n{inner}{name} {{'
        f'\n{inner}\tqcom,glink-channels = "IPCRTR";'
        f'\n{inner}\t{INTENTS}'
        f'\n{inner}\tqcom,no-wake-svc = <0x190>;'
        f'\n{inner}}};'
    )
    # append at the END of the node body (before its closing brace)
    t = t[:k] + insert + '\n' + indent + t[k:]
    added += 1
    print(f'  appended IPCRTR ({name}) to glink-edge with remote-pid {pid}')

if not added:
    print('nothing to add (already present in every glink-edge)')

open(P, 'w', encoding='utf-8', newline='\n').write(t)
print(f'done: {added} IPCRTR channel(s) added')

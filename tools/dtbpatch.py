#!/usr/bin/env python3
"""Patch the decompiled mainline TB128FU DTS so that TB331FC's ABL accepts it.

TB331FC's LinuxLoader hard-looks-up these DT paths (strings in LinuxLoader.efi):
    /reserved-memory/splash_region       0xab8bd
    /reserved-memory/demura_region_0     0xa14e7
    /reserved-memory/demura_region_1     0x9f237
    /soc/disp_rdump_region               0x9c468
    /soc/qcom,dsi-display-primary        0x9c44a
    /soc/qcom,dsi-display-secondary      0xa7cd5
    /soc/dsi_pll_codes                   0xa9f5a
    /mem-offline                         0xa13b2
    /ddr-regions                         0xab90d
    /memory  /soc/  /chosen  /cpus  /aliases

The TB128FU mainline DTS lacks the display/memory ones, which is why ABL
rejects it ("Splash region not found in device tree, powering down the
display and controller").  We add them with this device's real addresses,
taken from tb331fc_stock.dts:

    splash_region@5c000000   reg <0 0x5c000000 0 0xf00000>  label cont_splash_region
    disp_rdump_region@5c000000 reg <0 0x5c000000 0 0xf00000> label disp_rdump_region
"""
import re, sys, shutil

SRC = sys.argv[1] if len(sys.argv) > 1 else 'ref.dts'
DST = sys.argv[2] if len(sys.argv) > 2 else 'ref_patched.dts'

txt = open(SRC, encoding='utf-8').read()
orig_len = len(txt)

# ------------------------------------------------ 0. drop unit addresses
# The vendor DT (accepted by ABL) names its root nodes "memory" and "soc",
# with no unit address.  ABL looks up the *exact* paths "/memory" and
# "/soc/...".  A mainline DTB uses "memory@80000000" / "soc@0", so every one
# of those lookups misses.  Drop the unit address on both.
n = 0
for old, new in (('\tsoc@0 {\n', '\tsoc {\n'),
                 ('\tmemory@80000000 {\n', '\tmemory {\n')):
    if old in txt:
        txt = txt.replace(old, new, 1)
        n += 1
print(f'[ok] dropped unit address on {n} root node(s) (soc@0/memory@...)')

# ---------------------------------------------------------------- 1. splash
# mainline keeps the ABL framebuffer carveout as "memory@5c000000"; ABL wants
# the name "splash_region" plus the cont_splash_region label.
old_block = """		memory@5c000000 {
			reg = <0x00 0x5c000000 0x00 0xf00000>;
			no-map;
		};"""
new_block = """		splash_region@5c000000 {
			label = "cont_splash_region";
			reg = <0x00 0x5c000000 0x00 0xf00000>;
			no-map;
		};"""
if old_block in txt:
    txt = txt.replace(old_block, new_block, 1)
    print('[ok] renamed reserved-memory memory@5c000000 -> splash_region@5c000000 (+label)')
elif 'splash_region@5c000000' in txt:
    print('[skip] splash_region@5c000000 already present')
else:
    print('[WARN] could not locate the 0x5c000000 reserved-memory block')

# ------------------------------------------------- 2. /soc@0/disp_rdump_region
def insert_at_block_end(text, header, blob):
    """insert `blob` just before the closing brace of the block opened by `header`"""
    i = text.find(header)
    if i < 0:
        return text, False
    depth = 0
    j = text.index('{', i)
    k = j
    while k < len(text):
        c = text[k]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                line_start = text.rfind('\n', 0, k) + 1
                return text[:line_start] + blob + text[line_start:], True
        k += 1
    return text, False


soc_marker = '\tsoc {\n'
disp_node = ('\t\tdisp_rdump_region@5c000000 {\n'
             '\t\t\tlabel = "disp_rdump_region";\n'
             '\t\t\treg = <0x00 0x5c000000 0x00 0xf00000>;\n'
             '\t\t};\n\n')
if 'disp_rdump_region@5c000000' in txt:
    print('[skip] disp_rdump_region already present')
else:
    txt, ok = insert_at_block_end(txt, soc_marker, disp_node)
    print('[ok] added /soc/disp_rdump_region@5c000000 at end of soc'
          if ok else '[WARN] could not locate soc block')

# ----------------------- 2. /chosen pre-seeded props ABL rewrites in place
# LinuxLoader logs: "ERROR: Cannot update chosen node [linux,initrd-start] - 0x%x"
# The vendor DTB already contains these properties, so ABL only has to
# overwrite them.  A mainline DTB that lacks them forces ABL to grow the
# property list, which is the classic "ABL refuses to boot" trap.
chosen_marker = '\tchosen {\n'
chosen_props = ('\t\tlinux,initrd-start = <0x00 0x44986000>;\n'
                '\t\tlinux,initrd-end = <0x00 0x456fe3fc>;\n'
                '\t\tkaslr-seed = <0x00 0x00>;\n')
if 'linux,initrd-start' in txt:
    print('[skip] chosen already has linux,initrd-start')
elif chosen_marker in txt:
    txt = txt.replace(chosen_marker, chosen_marker + chosen_props, 1)
    print('[ok] pre-seeded /chosen with linux,initrd-start/end + kaslr-seed')
else:
    print('[WARN] could not find chosen node')

# ------------------------------------------- 3. root: /mem-offline /ddr-regions
root_nodes = """	mem-offline {
		compatible = "qcom,mem-offline";
		offline-sizes = <0x01 0x40000000 0x00 0x40000000 0x01 0xc0000000 0x00 0x80000000 0x02 0xc0000000 0x01 0x40000000>;
		granule = <0x200>;
	};

	ddr-regions {
	};

"""
aliases_marker = '\taliases {\n'
if 'mem-offline' in txt:
    print('[skip] mem-offline already present')
elif aliases_marker in txt:
    txt = txt.replace(aliases_marker, root_nodes + aliases_marker, 1)
    print('[ok] added root /mem-offline and /ddr-regions')
else:
    print('[WARN] could not find root aliases node to anchor root-level inserts')

open(DST, 'w', encoding='utf-8', newline='\n').write(txt)
print(f'wrote {DST}: {orig_len} -> {len(txt)} bytes')

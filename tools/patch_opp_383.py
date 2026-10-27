#!/usr/bin/env python3
"""patch_opp_383.py

The DPU OPP table inside the flashed vendor_boot says 384000000, but
dispcc-sm6225.c's ftbl_disp_cc_mdss_mdp_clk_src only offers **383000000**
(F(383000000, P_DISP_CC_PLL0_OUT_MAIN, 2, 0, 0)).  clk_set_rate(384000000)
therefore fails with -EINVAL and, worse, the failed transition leaves
disp_cc_mdss_mdp_clk at the 19.2 MHz minimum -> display starved -> stripes.

Patch the 8-byte big-endian opp-hz value in place:
    0x0000000016e36000  (384000000)  ->  0x0000000016d41dc0  (383000000)

384 MHz is PLL0/2 at the current parent, so set_rate() succeeds and the MDP
clock stays where the hardware is happy.  Same byte length, so the FDT is not
resized.
"""
import struct
import sys

src, dst = sys.argv[1], sys.argv[2]

data = bytearray(open(src, 'rb').read())

# locate the FDT (vendor_boot places the dtb on a page boundary)
FDT_MAGIC = b'\xd0\x0d\xfe\xed'
off = -1
for cand in range(0, len(data) - 4, 0x1000):
    if data[cand:cand + 4] == FDT_MAGIC:
        off = cand
        break
if off < 0:
    sys.exit('no FDT found in ' + src)

size = struct.unpack('>I', data[off + 4:off + 8])[0]
print(f'FDT at 0x{off:x}, size {size}')

OLD = bytes.fromhex('0000000016e36000')   # 384000000
NEW = bytes.fromhex('0000000016d41dc0')   # 383000000

region = bytes(data[off:off + size])
n = region.count(OLD)
print(f'occurrences of 384000000 in DTB: {n}')
if n != 1:
    sys.exit('expected exactly 1 occurrence, aborting')

i = region.index(OLD)
data[off + i:off + i + 8] = NEW
open(dst, 'wb').write(bytes(data))
print(f'patched at DTB offset 0x{i:x} -> {dst}')

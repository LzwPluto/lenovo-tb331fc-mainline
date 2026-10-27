import os
import re

mbn_path = r"D:\TB331FCLinux\firmware\dsp-squashed\adsp.mbn"
if not os.path.exists(mbn_path):
    # try nonhlos
    mbn_path = r"D:\TB331FCLinux\firmware\nonhlos\adsp.mdt"

print("Searching in:", mbn_path)
with open(mbn_path, "rb") as f:
    data = f.read()

# Search for common sensor chip names: bmi, bma, lsm, lis, icm, mpu, stk, tcs, sx, qmc, mmc
patterns = [b'bmi[0-9]+', b'bma[0-9]+', b'lsm[0-9a-z]+', b'lis[0-9a-z]+', b'icm[0-9]+', b'stk[0-9]+', b'tcs[0-9]+', b'sx9[0-9]+', b'qmc[0-9]+', b'mmc[0-9]+', b'sns_']
for p in patterns:
    matches = set(re.findall(p, data, re.IGNORECASE))
    if matches:
        print(f"Pattern {p}: {matches}")

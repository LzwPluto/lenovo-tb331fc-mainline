import re

mbn_path = r"D:\TB331FCLinux\firmware\dsp-squashed\adsp.mbn"
with open(mbn_path, "rb") as f:
    data = f.read()

matches = re.finditer(b'([a-zA-Z0-9_/.-]*(?:bmi3|icm4|sns_)[a-zA-Z0-9_/.-]*)', data, re.IGNORECASE)
found = set()
for m in matches:
    val = m.group(0).decode('latin1')
    if len(val) > 4:
        found.add(val)

print(f"Total matching sensor strings: {len(found)}")
for s in sorted(list(found))[:40]:
    print("  ", s)

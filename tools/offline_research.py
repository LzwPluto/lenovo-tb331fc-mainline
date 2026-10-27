import os
import re

vendor_dts_path = r"D:\TB331FCLinux\ref\android\vendor.dts"
dmesg_path = r"D:\TB331FCLinux\ref\android\android-dmesg.txt"
props_path = r"D:\TB331FCLinux\ref\android\dump-20261024-204843\props.txt"

print("==================== 1. SENSORS SEARCH IN VENDOR DTS ====================")
with open(vendor_dts_path, "r", encoding="utf-8", errors="ignore") as f:
    dts_text = f.read()

keywords = ['sensors', 'ssc', 'slpi', 'fastrpc', 'remoteproc', 'adsp', 'cdsp', 'qcom,ssc', 'qcom,sensors']
for kw in keywords:
    matches = [line.strip() for line in dts_text.splitlines() if kw in line.lower()]
    print(f"Keyword '{kw}': {len(matches)} occurrences")
    for m in matches[:5]:
        print(f"   {m}")

print("\n==================== 2. SENSORS SEARCH IN ANDROID DMESG ====================")
if os.path.exists(dmesg_path):
    with open(dmesg_path, "r", encoding="utf-8", errors="ignore") as f:
        dmesg_text = f.read()
    sensor_lines = [line.strip() for line in dmesg_text.splitlines() if any(k in line.lower() for k in ['sensor', 'accel', 'gyro', 'als', 'ssc', 'slpi', 'sc8960', 'rt1711', 'aw35615', 'pm8008'])]
    print(f"Total matching dmesg lines: {len(sensor_lines)}")
    # Print distinct drivers / tags
    tags = set()
    for l in sensor_lines:
        m = re.search(r'\[\s*\d+\.\d+\]\s*([^:]+):', l)
        if m:
            tags.add(m.group(1).strip())
    print("Found dmesg tags:", tags)
    print("\nSample lines:")
    for l in sensor_lines[:25]:
        print(f"   {l}")

print("\n==================== 3. SENSORS & POWER IN PROPS ====================")
if os.path.exists(props_path):
    with open(props_path, "r", encoding="utf-8", errors="ignore") as f:
        props_text = f.read()
    matching_props = [l.strip() for l in props_text.splitlines() if any(k in l.lower() for k in ['sensor', 'charge', 'battery', 'audio', 'sound', 'camera', 'bluetooth'])]
    print(f"Matching props count: {len(matching_props)}")
    for l in matching_props[:30]:
        print(f"   {l}")

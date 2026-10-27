import os
import re

dmesg_path = r"D:\TB331FCLinux\ref\android\android-dmesg.txt"

print("==================== ANDROID DMESG ANALYSIS (UTF-16) ====================")
with open(dmesg_path, "r", encoding="utf-16", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines in dmesg: {len(lines)}")

# Let's search for interesting subsystems
searches = {
    "Charging & Power": ['sc8960', 'charge', 'smb', 'battery', 'mm8013', 'psy', 'power_supply', 'tcpm', 'rt1711', 'aw35615', 'fsa4480'],
    "Sensors & SSC": ['sensor', 'accel', 'gyro', 'als', 'proximity', 'ssc', 'slpi', 'sns_', 'stk', 'bmi', 'icm'],
    "Audio & DSP": ['aw88166', 'aw883xx', 'audio', 'sound', 'codec', 'bolero', 'wcd', 'apr', 'gpr', 'q6', 'adsp', 'cdsp'],
    "Camera": ['camera', 'camss', 'cci', 'sensor_probe', 'ov13b', 'ov08d', 'gc08a', 'actuator', 'eeprom'],
    "Input & Keys": ['gpio-keys', 'hall', 'lid', 'kpdpwr', 'resin', 'pen', 'stylus', 'pogo']
}

for cat, terms in searches.items():
    print(f"\n--- {cat} ---")
    matches = [l.strip() for l in lines if any(t in l.lower() for t in terms)]
    print(f"Count: {len(matches)}")
    # Distinct prefixes
    prefixes = set()
    for l in matches:
        m = re.search(r'\[\s*\d+\.\d+\]\s*([^:]+):', l)
        if m:
            prefixes.add(m.group(1).strip())
    print(f"Drivers/Tags: {list(prefixes)[:10]}")
    # Show first 8 matching lines
    for l in matches[:8]:
        print(f"  {l[:140]}")

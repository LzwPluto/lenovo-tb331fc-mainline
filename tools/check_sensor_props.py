with open(r"D:\TB331FCLinux\ref\android\dump-20261024-204843\props.txt", "r", encoding="utf-8", errors="ignore") as f:
    props = f.read()

sensor_props = [l.strip() for l in props.splitlines() if 'sensor' in l.lower() or 'ssc' in l.lower() or 'slpi' in l.lower() or 'motion' in l.lower()]
print(f"Total sensor props: {len(sensor_props)}")
for p in sensor_props:
    print("  ", p)

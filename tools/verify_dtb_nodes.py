with open(r"D:\TB331FCLinux\build\CANONICAL_ktz.dtb", "rb") as f:
    data = f.read()

checks = [b"aw88166", b"aw883xx_acf.bin", b"fsa4480", b"rt1711h", b"mm8013", b"hall-sensor", b"sy6974"]
for c in checks:
    present = c in data
    print(f"{c.decode('latin1')}: {'PRESENT' if present else 'NOT FOUND'}")

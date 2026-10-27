with open(r"D:\TB331FCLinux\ref\android\android-dmesg.txt", "rb") as f:
    raw = f.read(200)
    print("First 200 bytes:", raw)

import struct

d = open(r"D:\TB331FCLinux\build\vb_spidma.img", "rb").read()
tbl = 0x322000
print("Bytes at 0x322000 in vb_spidma.img:")
print([hex(x) for x in d[tbl:tbl+32]])
print("size field:", struct.unpack_from('<I', d, tbl)[0])
print("offset field:", struct.unpack_from('<I', d, tbl+4)[0])
print("type field:", struct.unpack_from('<I', d, tbl+8)[0])
print("header vr_size:", struct.unpack_from('<I', d, 0x18)[0])

path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\codecs\aw88166.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("static struct i2c_driver")
print(text[idx:idx+350])

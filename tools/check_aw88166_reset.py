path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\codecs\aw88166.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("reset")
while idx != -1:
    line_start = text.rfind('\n', 0, idx)
    line_end = text.find('\n', idx)
    print(text[line_start:line_end].strip())
    idx = text.find("reset", idx + 1)

path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_ts.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'int32_t nvt_ts_suspend\(struct device \*dev\)', text)]
print("Suspend definitions at:", matches)
if len(matches) > 1:
    pos = matches[1]
    print(text[pos:pos+1500])

matches_res = [m.start() for m in re.finditer(r'int32_t nvt_ts_resume\(struct device \*dev\)', text)]
print("Resume definitions at:", matches_res)
if len(matches_res) > 1:
    pos = matches_res[1]
    print(text[pos:pos+1500])

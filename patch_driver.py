import os

path_ts = "/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c"
with open(path_ts, "r") as f:
    s = f.read()

old = "pen_battery = (uint32_t)point_data[78];"
new = old + "\n\t\t\tNVT_LOG(\"PEN EVENT: x=%d y=%d pressure=%d dist=%d\\n\", pen_x, pen_y, pen_pressure, pen_distance);"

if old in s and "PEN EVENT:" not in s:
    s = s.replace(old, new, 1)
    with open(path_ts, "w") as f:
        f.write(s)
    print("Added PEN EVENT log successfully")
else:
    print("PEN EVENT log already present or target not found")

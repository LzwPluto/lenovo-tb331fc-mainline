#!/usr/bin/env python3
"""patch_mm8013.py

Updates drivers/power/supply/mm8013.c to support TB331FC:
1. Adds compatible strings 'mm8013c10' and 'mitsumi,mm8013c10'
2. Adds graceful fallback if battery ID differs from stock 101/102.
"""
import sys

path = "/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/power/supply/mm8013.c"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

target1 = """\tif (val == BATID_102)
\t\tbattery_id = 2;
\telse if (val == BATID_101)
\t\tbattery_id = 1;
\telse
\t\treturn -EINVAL;"""

repl1 = """\tif (val == BATID_102)
\t\tbattery_id = 2;
\telse if (val == BATID_101)
\t\tbattery_id = 1;
\telse {
\t\tdev_warn(&chip->client->dev, "unknown battery_id 0x%04x, proceeding with default (1)\\n", val);
\t\tbattery_id = 1;
\t}"""

target2 = """static const struct i2c_device_id mm8013_id_table[] = {
\t{ "mm8013" },
\t{}
};
MODULE_DEVICE_TABLE(i2c, mm8013_id_table);

static const struct of_device_id mm8013_match_table[] = {
\t{ .compatible = "mitsumi,mm8013" },
\t{}
};"""

repl2 = """static const struct i2c_device_id mm8013_id_table[] = {
\t{ "mm8013" },
\t{ "mm8013c10" },
\t{}
};
MODULE_DEVICE_TABLE(i2c, mm8013_id_table);

static const struct of_device_id mm8013_match_table[] = {
\t{ .compatible = "mitsumi,mm8013" },
\t{ .compatible = "mitsumi,mm8013c10" },
\t{ .compatible = "mm8013c10" },
\t{}
};"""

if repl1 in c and repl2 in c:
    print("mm8013.c is already patched")
    sys.exit(0)

if target1 not in c or target2 not in c:
    print("ERROR: Target patterns not found in mm8013.c")
    sys.exit(1)

c = c.replace(target1, repl1, 1).replace(target2, repl2, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(c)

print("mm8013.c patched successfully")

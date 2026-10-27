#!/usr/bin/env python3
"""patch_aw88166_compat.py

Patches sound/soc/codecs/aw88166.c to be compatible with Linux 6.14:
- Defines AW_DSP_16_DATA / AW_DSP_32_DATA -> AW88395_DSP_*
- Defines system_dfl_wq -> system_wq
- Implements aw_dev_dsp_read / aw_dev_dsp_write
"""
import sys

path = "/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/sound/soc/codecs/aw88166.c"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

helpers = """
#ifndef AW_DSP_16_DATA
#define AW_DSP_16_DATA AW88395_DSP_16_DATA
#define AW_DSP_32_DATA AW88395_DSP_32_DATA
#endif

#ifndef system_dfl_wq
#define system_dfl_wq system_wq
#endif

static int aw_dev_dsp_write_16bit(struct aw_device *aw_dev,
\t\tunsigned short dsp_addr, unsigned int dsp_data)
{
\tint ret;

\tret = regmap_write(aw_dev->regmap, AW88166_DSPMADD_REG, dsp_addr);
\tif (ret) {
\t\tdev_err(aw_dev->dev, "%s write addr error, ret=%d\\n", __func__, ret);
\t\treturn ret;
\t}

\tret = regmap_write(aw_dev->regmap, AW88166_DSPMDAT_REG, (u16)dsp_data);
\tif (ret) {
\t\tdev_err(aw_dev->dev, "%s write data error, ret=%d\\n", __func__, ret);
\t\treturn ret;
\t}

\treturn 0;
}

static int aw_dev_dsp_write(struct aw_device *aw_dev,
\t\tunsigned short dsp_addr, unsigned int dsp_data, unsigned char data_type)
{
\tint ret;

\tmutex_lock(&aw_dev->dsp_lock);
\tswitch (data_type) {
\tcase AW_DSP_16_DATA:
\t\tret = aw_dev_dsp_write_16bit(aw_dev, dsp_addr, dsp_data);
\t\tif (ret)
\t\t\tdev_err(aw_dev->dev, "write dsp_addr[0x%x] 16-bit dsp_data[0x%x] failed\\n",
\t\t\t\t\t(u32)dsp_addr, dsp_data);
\t\tbreak;
\tdefault:
\t\tdev_err(aw_dev->dev, "data type[%d] unsupported\\n", data_type);
\t\tret = -EINVAL;
\t\tbreak;
\t}
\tmutex_unlock(&aw_dev->dsp_lock);

\treturn ret;
}

static int aw_dev_dsp_read_16bit(struct aw_device *aw_dev,
\t\tunsigned short dsp_addr, unsigned int *dsp_data)
{
\tunsigned int temp_data;
\tint ret;

\tret = regmap_write(aw_dev->regmap, AW88166_DSPMADD_REG, dsp_addr);
\tif (ret) {
\t\tdev_err(aw_dev->dev, "%s write error, ret=%d\\n", __func__, ret);
\t\treturn ret;
\t}

\tret = regmap_read(aw_dev->regmap, AW88166_DSPMDAT_REG, &temp_data);
\tif (ret) {
\t\tdev_err(aw_dev->dev, "%s read error, ret=%d\\n", __func__, ret);
\t\treturn ret;
\t}
\t*dsp_data = temp_data;

\treturn 0;
}

static int aw_dev_dsp_read_32bit(struct aw_device *aw_dev,
\t\tunsigned short dsp_addr, unsigned int *dsp_data)
{
\tunsigned int temp_data;
\tint ret;

\tret = regmap_write(aw_dev->regmap, AW88166_DSPMADD_REG, dsp_addr);
\tif (ret) {
\t\tdev_err(aw_dev->dev, "%s write error, ret=%d\\n", __func__, ret);
\t\treturn ret;
\t}

\tret = regmap_read(aw_dev->regmap, AW88166_DSPMDAT_REG, &temp_data);
\tif (ret) {
\t\tdev_err(aw_dev->dev, "%s read error, ret=%d\\n", __func__, ret);
\t\treturn ret;
\t}
\t*dsp_data = temp_data;

\tret = regmap_read(aw_dev->regmap, AW88166_DSPMDAT_REG, &temp_data);
\tif (ret) {
\t\tdev_err(aw_dev->dev, "%s read error, ret=%d\\n", __func__, ret);
\t\treturn ret;
\t}
\t*dsp_data |= (temp_data << 16);

\treturn 0;
}

static int aw_dev_dsp_read(struct aw_device *aw_dev,
\t\tunsigned short dsp_addr, unsigned int *dsp_data, unsigned char data_type)
{
\tint ret;

\tmutex_lock(&aw_dev->dsp_lock);
\tswitch (data_type) {
\tcase AW_DSP_16_DATA:
\t\tret = aw_dev_dsp_read_16bit(aw_dev, dsp_addr, dsp_data);
\t\tif (ret)
\t\t\tdev_err(aw_dev->dev, "read dsp_addr[0x%x] 16-bit dsp_data[0x%x] failed\\n",
\t\t\t\t\t(u32)dsp_addr, *dsp_data);
\t\tbreak;
\tcase AW_DSP_32_DATA:
\t\tret = aw_dev_dsp_read_32bit(aw_dev, dsp_addr, dsp_data);
\t\tif (ret)
\t\t\tdev_err(aw_dev->dev, "read dsp_addr[0x%x] 32-bit dsp_data[0x%x] failed\\n",
\t\t\t\t\t(u32)dsp_addr, *dsp_data);
\t\tbreak;
\tdefault:
\t\tdev_err(aw_dev->dev, "data type[%d] unsupported\\n", data_type);
\t\tret = -EINVAL;
\t\tbreak;
\t}
\tmutex_unlock(&aw_dev->dsp_lock);

\treturn ret;
}
"""

anchor = '#include "aw88395/aw88395_device.h"\n'
if "#define AW_DSP_16_DATA" in c:
    print("Already patched")
    sys.exit(0)

if anchor not in c:
    print("Anchor not found!")
    sys.exit(1)

c = c.replace(anchor, anchor + helpers, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(c)

print("aw88166.c patched successfully!")

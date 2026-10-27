path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\codecs\aw88166.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add fallback in request_firmware
old_fw = """\tret = request_firmware(&cont, fw_name, aw88166->aw_pa->dev);
\tif (ret) {
\t\tdev_err(aw88166->aw_pa->dev, "request [%s] failed!\\n", fw_name);
\t\treturn ret;
\t}"""

new_fw = """\tret = request_firmware(&cont, fw_name, aw88166->aw_pa->dev);
\tif (ret && strcmp(fw_name, "aw883xx_acf.bin") != 0) {
\t\tfw_name = "aw883xx_acf.bin";
\t\tret = request_firmware(&cont, fw_name, aw88166->aw_pa->dev);
\t}
\tif (ret) {
\t\tdev_err(aw88166->aw_pa->dev, "request [%s] failed!\\n", fw_name);
\t\treturn ret;
\t}"""

if old_fw in text:
    text = text.replace(old_fw, new_fw, 1)
    print("Patched request_firmware with fallback")
else:
    print("old_fw pattern not found or already patched")

# 2. Add of_device_id
of_match_code = """
static const struct of_device_id aw88166_of_match[] = {
\t{ .compatible = "awinic,aw88166" },
\t{ .compatible = "awinic,aw883xx_smartpa" },
\t{ }
};
MODULE_DEVICE_TABLE(of, aw88166_of_match);
"""

old_driver = """static struct i2c_driver aw88166_i2c_driver = {
\t.driver = {
\t\t.name = AW88166_I2C_NAME,
\t},"""

new_driver = of_match_code + """static struct i2c_driver aw88166_i2c_driver = {
\t.driver = {
\t\t.name = AW88166_I2C_NAME,
\t\t.of_match_table = of_match_ptr(aw88166_of_match),
\t},"""

if old_driver in text:
    text = text.replace(old_driver, new_driver, 1)
    print("Added of_match_table to aw88166_i2c_driver")
else:
    print("old_driver pattern not found or already patched")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("enhance_aw88166.py finished!")

import sys

def patch_panel():
    path = "/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c"
    with open(path, "r") as f:
        content = f.read()

    if "inverted_dbv" in content:
        print("panel-himax-hx83102.c already patched.")
        return

    # 1. Update struct hx83102_panel_desc
    old_desc = "\tbool has_dcs_backlight;\n\tbool has_dsc;"
    new_desc = "\tbool has_dcs_backlight;\n\tbool inverted_dbv;\n\tbool has_dsc;"
    assert old_desc in content, "old_desc not found"
    content = content.replace(old_desc, new_desc, 1)

    # 2. Update lenovo_p255_inx_desc
    old_inx = """static const struct hx83102_panel_desc lenovo_p255_inx_desc = {
\t.modes = &lenovo_p255_inx_mode,
\t.size = {
\t\t.width_mm = 147,
\t\t.height_mm = 235,
\t},
\t.has_dcs_backlight = true,"""
    new_inx = """static const struct hx83102_panel_desc lenovo_p255_inx_desc = {
\t.modes = &lenovo_p255_inx_mode,
\t.size = {
\t\t.width_mm = 147,
\t\t.height_mm = 235,
\t},
\t.has_dcs_backlight = true,
\t.inverted_dbv = true,"""
    assert old_inx in content, "old_inx not found"
    content = content.replace(old_inx, new_inx, 1)

    # 3. Update hx83102_bl_update_status and hx83102_backlight_register
    old_bl = """static int hx83102_bl_update_status(struct backlight_device *bl)
{
\tstruct mipi_dsi_device *dsi = bl_get_data(bl);
\tu16 brightness = backlight_get_brightness(bl);
\tint ret;

\tdsi->mode_flags &= ~MIPI_DSI_MODE_LPM;

\tret = mipi_dsi_dcs_set_display_brightness_large(dsi, brightness);
\tif (ret < 0)
\t\treturn ret;

\tdsi->mode_flags |= MIPI_DSI_MODE_LPM;

\treturn 0;
}

static const struct backlight_ops hx83102_bl_ops = {
\t.update_status = hx83102_bl_update_status,
};

static struct backlight_device *hx83102_backlight_register(struct hx83102 *ctx)
{
\tstruct device *dev = &ctx->dsi->dev;
\tconst struct backlight_properties props = {
\t\t.type = BACKLIGHT_RAW,
\t\t.brightness = 3767,
\t\t.max_brightness = 3767,
\t\t.scale = BACKLIGHT_SCALE_NON_LINEAR,
\t};

\treturn devm_backlight_device_register(dev, dev_name(dev), dev,
\t\t\t\t\t      ctx->dsi, &hx83102_bl_ops,
\t\t\t\t\t      &props);
}"""

    new_bl = """static int hx83102_bl_update_status(struct backlight_device *bl)
{
\tstruct hx83102 *ctx = bl_get_data(bl);
\tu16 brightness = backlight_get_brightness(bl);

\tif (ctx->desc->inverted_dbv)
\t\tbrightness = ((brightness & 0xff) << 8) | (brightness >> 8);

\treturn mipi_dsi_dcs_set_display_brightness_large(ctx->dsi, brightness);
}

static const struct backlight_ops hx83102_bl_ops = {
\t.update_status = hx83102_bl_update_status,
};

static struct backlight_device *hx83102_backlight_register(struct hx83102 *ctx)
{
\tstruct device *dev = &ctx->dsi->dev;
\tconst struct backlight_properties props = {
\t\t.type = BACKLIGHT_RAW,
\t\t.brightness = 2048,
\t\t.max_brightness = 4095,
\t\t.scale = BACKLIGHT_SCALE_NON_LINEAR,
\t};

\treturn devm_backlight_device_register(dev, dev_name(dev), dev,
\t\t\t\t\t      ctx, &hx83102_bl_ops,
\t\t\t\t\t      &props);
}"""
    assert old_bl in content, "old_bl not found"
    content = content.replace(old_bl, new_bl, 1)

    with open(path, "w") as f:
        f.write(content)
    print("panel-himax-hx83102.c patched successfully!")

def patch_touch():
    h_path = "/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523.h"
    with open(h_path, "r") as f:
        h_content = f.read()
    h_content = h_content.replace("#define NVT_TOUCH_WDT_RECOVERY 0", "#define NVT_TOUCH_WDT_RECOVERY 1")
    with open(h_path, "w") as f:
        f.write(h_content)
    print("nt36523.h patched successfully!")

    c_path = "/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c"
    with open(c_path, "r") as f:
        c_content = f.read()

    # Forward declare nvt_panel_on_work and nvt_panel_work before nvt_ts_work_func
    fwd_marker = "irqreturn_t nvt_ts_work_func(int irq, void *data)\n{"
    fwd_decl = """static void nvt_panel_on_work(struct work_struct *work);
static DECLARE_WORK(nvt_panel_work, nvt_panel_on_work);

irqreturn_t nvt_ts_work_func(int irq, void *data)
{"""
    assert fwd_marker in c_content, "fwd_marker not found"
    c_content = c_content.replace(fwd_marker, fwd_decl, 1)

    # In nvt_panel_on_work (original definition later in file), remove the old DECLARE_WORK so there is no duplicate
    old_decl_work = "static DECLARE_WORK(nvt_panel_work, nvt_panel_on_work);"
    # It appears twice now (the one we added + original). Replace the second one with empty or comment.
    idx1 = c_content.find(old_decl_work)
    idx2 = c_content.find(old_decl_work, idx1 + len(old_decl_work))
    if idx2 != -1:
        c_content = c_content[:idx2] + "/* nvt_panel_work declared above */" + c_content[idx2 + len(old_decl_work):]

    # In nvt_ts_work_func, replace WDT recovery block
    old_wdt_block = """#if NVT_TOUCH_WDT_RECOVERY
\t/* Controller WDT reset recovery (0xFD / 0xFE) */
\t{
\t\t/* vendor: bytes 1..6 must all be 0xFD/0xFE, i.e. (b + 3) & 0xFF <= 1 */
\t\tstatic unsigned int err_run;
\t\tbool all_err = true;
\t\tint k;

\t\tfor (k = 1; k <= 6; k++) {
\t\t\tif (((point_data[k] + 3) & 0xFF) > 1) {
\t\t\t\tall_err = false;
\t\t\t\tbreak;
\t\t\t}
\t\t}

\t\tif (all_err) {
\t\t\terr_run++;
\t\t\tif (err_run > 10) {
\t\t\t\terr_run = 0;
\t\t\t\tif (point_data[1] != 0xFE) {
\t\t\t\t\tNVT_ERR("fw reload after error run (0x%02X)\\n",
\t\t\t\t\t\tpoint_data[1]);
\t\t\t\t\tnvt_update_firmware(ts->fw_name);
\t\t\t\t\tnvt_check_fw_reset_state(RESET_STATE_REK);
\t\t\t\t\tnvt_restore_cmd_func();
\t\t\t\t} else {
\t\t\t\t\tNVT_ERR("got 0xFE run -> reset to idle\\n");
\t\t\t\t\tnvt_sw_reset_idle();
\t\t\t\t\tmsleep(15);
\t\t\t\t\tnvt_restore_cmd_func();
\t\t\t\t}
\t\t\t}
\t\t\tgoto XFER_ERROR;
\t\t}
\t\terr_run = 0;
\t}
#endif"""

    new_wdt_block = """#if NVT_TOUCH_WDT_RECOVERY
\t/* Controller WDT / ESD reset recovery (0xFD / 0xFE) */
\t{
\t\t/* vendor: bytes 1..6 must all be 0xFD/0xFE, i.e. (b + 3) & 0xFF <= 1 */
\t\tstatic unsigned int err_run;
\t\tbool all_err = true;
\t\tint k;

\t\tfor (k = 1; k <= 6; k++) {
\t\t\tif (((point_data[k] + 3) & 0xFF) > 1) {
\t\t\t\tall_err = false;
\t\t\t\tbreak;
\t\t\t}
\t\t}

\t\tif (all_err) {
\t\t\terr_run++;
\t\t\tif (err_run > 5) {
\t\t\t\terr_run = 0;
\t\t\t\tNVT_ERR("ESD/WDT reset detected (0x%02X), scheduling async recovery!\\n",
\t\t\t\t\tpoint_data[1]);
\t\t\t\tnvt_irq_enable(false);
\t\t\t\tschedule_work(&nvt_panel_work);
\t\t\t}
\t\t\tgoto XFER_ERROR;
\t\t}
\t\terr_run = 0;
\t}
#endif"""

    assert old_wdt_block in c_content, "old_wdt_block not found"
    c_content = c_content.replace(old_wdt_block, new_wdt_block, 1)

    # Rate-limit packet csum mismatch print
    old_csum_block = """\t/* Checksum verification (64 bytes touch buffer) */
\tcsum = 0;
\tfor (i = 0; i < 64; i++) {
\t\tcsum += point_data[1 + i];
\t}
\tif (((uint8_t)(-csum)) != point_data[65]) {
\t\t{
\t\t\tstatic unsigned long last_dump;
\t\t\tif (time_after(jiffies, last_dump + msecs_to_jiffies(1000))) {
\t\t\t\tlast_dump = jiffies;
\t\t\t\tNVT_LOG("pkt rejected, raw: %*ph\\n",
\t\t\t\t\t10, point_data + 1);
\t\t\t}
\t\t}
\t\t{
\t\t\tstatic unsigned long last_dump;
\t\t\tif (time_after(jiffies, last_dump + msecs_to_jiffies(1000))) {
\t\t\t\tlast_dump = jiffies;
\t\t\t\tNVT_LOG("pkt rejected, raw: %*ph\\n",
\t\t\t\t\t10, point_data + 1);
\t\t\t}
\t\t}
\t\t{
\t\t\tstatic unsigned long last_dump;
\t\t\tif (time_after(jiffies, last_dump + msecs_to_jiffies(1000))) {
\t\t\t\tlast_dump = jiffies;
\t\t\t\tNVT_LOG("pkt rejected, raw: %*ph\\n",
\t\t\t\t\t10, point_data + 1);
\t\t\t}
\t\t}
\t\tNVT_LOG("packet csum mismatch: calc=0x%02X != 0x%02X, raw: %*ph\\n",
\t\t\t(uint8_t)(-csum), point_data[65], 8, point_data + 1);
\t\tgoto XFER_ERROR;
\t}"""

    new_csum_block = """\t/* Checksum verification (64 bytes touch buffer) */
\tcsum = 0;
\tfor (i = 0; i < 64; i++) {
\t\tcsum += point_data[1 + i];
\t}
\tif (((uint8_t)(-csum)) != point_data[65]) {
\t\tstatic unsigned long last_dump;
\t\tif (time_after(jiffies, last_dump + msecs_to_jiffies(1000))) {
\t\t\tlast_dump = jiffies;
\t\t\tNVT_LOG("packet csum mismatch: calc=0x%02X != 0x%02X, raw: %*ph\\n",
\t\t\t\t(uint8_t)(-csum), point_data[65], 8, point_data + 1);
\t\t}
\t\tgoto XFER_ERROR;
\t}"""

    assert old_csum_block in c_content, "old_csum_block not found"
    c_content = c_content.replace(old_csum_block, new_csum_block, 1)

    with open(c_path, "w") as f:
        f.write(c_content)
    print("nt36523_ts.c patched successfully!")

if __name__ == "__main__":
    patch_panel()
    patch_touch()

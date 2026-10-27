import os

TS_PATH = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_ts.c"
FW_PATH = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_fw_update.c"

# --- 1. Patch nt36523_ts.c ---
with open(TS_PATH, "r", encoding="utf-8") as f:
    ts_code = f.read()

# Replace nvt_fw_crc_enable
old_fw_crc = """void nvt_fw_crc_enable(void)
{
	uint8_t buf[4] = {0};

	//---set xdata index to EVENT BUF ADDR---
	nvt_set_page(ts->mmap->EVENT_BUF_ADDR);

	//---clear fw reset status---
	buf[0] = EVENT_MAP_RESET_COMPLETE & (0x7F);
	buf[1] = 0x00;
	CTP_SPI_WRITE(ts->client, buf, 2);

	//---enable fw crc---
	buf[0] = EVENT_MAP_HOST_CMD & (0x7F);
	buf[1] = 0xAE;	//enable fw crc command
	CTP_SPI_WRITE(ts->client, buf, 2);
}"""

new_fw_crc = """void nvt_fw_crc_enable(void)
{
	uint8_t buf[8] = {0};

	//---set xdata index to EVENT BUF ADDR---
	nvt_set_page(ts->mmap->EVENT_BUF_ADDR);

	//---clear fw reset status---
	buf[0] = EVENT_MAP_RESET_COMPLETE & (0x7F);
	memset(&buf[1], 0, 6);
	CTP_SPI_WRITE(ts->client, buf, 7);

	//---enable fw crc---
	buf[0] = EVENT_MAP_HOST_CMD & (0x7F);
	buf[1] = 0xAE;	//enable fw crc command
	buf[2] = 0x00;
	CTP_SPI_WRITE(ts->client, buf, 3);
}"""
assert old_fw_crc in ts_code, "old_fw_crc not found in nt36523_ts.c"
ts_code = ts_code.replace(old_fw_crc, new_fw_crc)

# Replace nvt_boot_ready delay
old_boot_ready = """void nvt_boot_ready(void)
{
	//---write BOOT_RDY status cmds---
	nvt_write_addr(ts->mmap->BOOT_RDY_ADDR, 1);

	mdelay(5);"""

new_boot_ready = """void nvt_boot_ready(void)
{
	//---write BOOT_RDY status cmds---
	nvt_write_addr(ts->mmap->BOOT_RDY_ADDR, 1);

	udelay(100);"""
assert old_boot_ready in ts_code, "old_boot_ready not found in nt36523_ts.c"
ts_code = ts_code.replace(old_boot_ready, new_boot_ready)

# Replace nvt_ts_check_chip_ver_trim body
old_trim = """	ts->mmap = &NT36523_memory_map;
	ts->carrier_system = NT36523_hw_info.carrier_system;
	ts->hw_crc = NT36523_hw_info.hw_crc;
	return 0;
}"""

new_trim = """	for (list = 0; list < ARRAY_SIZE(trim_id_table); list++) {
		bool match = true;
		for (i = 0; i < NVT_ID_BYTE_MAX; i++) {
			if (trim_id_table[list].mask[i] &&
			    (buf[1 + i] != trim_id_table[list].id[i])) {
				match = false;
				break;
			}
		}
		if (match) {
			ts->mmap = trim_id_table[list].mmap;
			ts->carrier_system = trim_id_table[list].hwinfo->carrier_system;
			ts->hw_crc = trim_id_table[list].hwinfo->hw_crc;
			NVT_LOG("matched trim_id_table[%d], carrier=%d, hw_crc=%d, EVENT_BUF=0x%06X\\n",
				list, ts->carrier_system, ts->hw_crc, ts->mmap->EVENT_BUF_ADDR);
			return 0;
		}
	}

	NVT_ERR("no matching trim ID found!\\n");
	return -EINVAL;
}"""

assert old_trim in ts_code, "old_trim not found in nt36523_ts.c"
ts_code = ts_code.replace("int32_t retry;\n", "int32_t retry, list, i;\n")
ts_code = ts_code.replace(old_trim, new_trim)

with open(TS_PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write(ts_code)
print("nt36523_ts.c patched successfully!")


# --- 2. Patch nt36523_fw_update.c ---
with open(FW_PATH, "r", encoding="utf-8") as f:
    fw_code = f.read()

# Add nvt_spi_dma_setup before nvt_download_firmware_hw_crc
dma_setup_func = """static void nvt_spi_dma_setup(void)
{
	uint8_t buf[64] = {0};

	if (!ts->mmap->SPI_DMA_SETUP_ADDR)
		return;

	/* 1. Clear 32 bytes at DLM SRAM address */
	if (partition > 1 && bin_map) {
		nvt_set_page(bin_map[1].SRAM_addr);
		buf[0] = bin_map[1].SRAM_addr & 0x7F;
		memset(&buf[1], 0, 32);
		CTP_SPI_WRITE(ts->client, buf, 33);
	}

	/* 2. Write 0x00AA3235 to SPI_DMA_SETUP_ADDR (0x3F7D0) */
	nvt_set_page(ts->mmap->SPI_DMA_SETUP_ADDR);
	buf[0] = ts->mmap->SPI_DMA_SETUP_ADDR & 0x7F;
	buf[1] = 0x35;
	buf[2] = 0x32;
	buf[3] = 0xAA;
	buf[4] = 0x00;
	CTP_SPI_WRITE(ts->client, buf, 5);

	NVT_LOG("set spi dma val finish\\n");
}

"""

old_dl_func = """static int32_t nvt_download_firmware_hw_crc(void)
{
	uint8_t retry = 0;
	int32_t ret = 0;

	start = ktime_get();

	while (1) {
		/* bootloader reset to reset MCU */
		nvt_bootloader_reset();

		/* set ilm & dlm reg bank */
		nvt_set_bld_hw_crc();

		/* Start to write firmware process */
		if (cascade_2nd_header_info) {
			/* for cascade */
			nvt_tx_auto_copy_mode();

			ret = nvt_write_firmware(fw_entry->data, fw_entry->size);
			if (ret) {
				NVT_ERR("Write_Firmware failed. (%d)\\n", ret);
				goto fail;
			}

			ret = nvt_check_spi_dma_tx_info();
			if (ret) {
				NVT_ERR("spi dma tx info failed. (%d)\\n", ret);
				goto fail;
			}
		} else {
			ret = nvt_write_firmware(fw_entry->data, fw_entry->size);
			if (ret) {
				NVT_ERR("Write_Firmware failed. (%d)\\n", ret);
				goto fail;
			}
		}

		/* enable hw bld crc function */
		nvt_bld_crc_enable();

		/* clear fw reset status & enable fw crc check */
		nvt_fw_crc_enable();

		/* Set Boot Ready Bit */
		nvt_boot_ready();

		ret = nvt_check_fw_reset_state(RESET_STATE_INIT);
		if (ret) {
			NVT_ERR("nvt_check_fw_reset_state failed. (%d)\\n", ret);
			goto fail;
		} else {
			break;
		}"""

new_dl_func = dma_setup_func + """static int32_t nvt_download_firmware_hw_crc(void)
{
	uint8_t retry = 0;
	int32_t ret = 0;

	start = ktime_get();

	while (1) {
		/* bootloader reset to reset MCU */
		nvt_bootloader_reset();

		/* set ilm & dlm reg bank */
		nvt_set_bld_hw_crc();

		/* setup SPI DMA for NT36523N */
		nvt_spi_dma_setup();

		/* Start to write firmware process */
		if (cascade_2nd_header_info) {
			/* for cascade / auto copy */
			nvt_tx_auto_copy_mode();

			ret = nvt_write_firmware(fw_entry->data, fw_entry->size);
			if (ret) {
				NVT_ERR("Write_Firmware failed. (%d)\\n", ret);
				goto fail;
			}

			ret = nvt_check_spi_dma_tx_info();
			if (ret) {
				NVT_ERR("spi dma tx info failed. (%d)\\n", ret);
				goto fail;
			}
		} else {
			ret = nvt_write_firmware(fw_entry->data, fw_entry->size);
			if (ret) {
				NVT_ERR("Write_Firmware failed. (%d)\\n", ret);
				goto fail;
			}
		}

		/* clear fw reset status & enable fw crc check */
		nvt_fw_crc_enable();

		/* Set Boot Ready Bit */
		nvt_boot_ready();

		ret = nvt_check_fw_reset_state(RESET_STATE_INIT);
		if (ret) {
			NVT_ERR("nvt_check_fw_reset_state failed. (%d)\\n", ret);
			goto fail;
		} else {
			break;
		}"""

assert old_dl_func in fw_code, "old_dl_func not found in nt36523_fw_update.c"
fw_code = fw_code.replace(old_dl_func, new_dl_func)

with open(FW_PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write(fw_code)
print("nt36523_fw_update.c patched successfully!")

/*
 * INTEL CONFIDENTIAL
 *
 * Copyright (C) 2021-2024 Intel Corporation
 *
 * This software and the related documents are Intel copyrighted materials,
 * and your use of them is governed by the express license under which they
 * were provided to you ("License"). Unless the License provides otherwise,
 * you may not use, modify, copy, publish, distribute, disclose or transmit
 * this software or the related documents without Intel's prior written permission.
 * This software and the related documents are provided as is, with no express
 * or implied warranties, other than those that are expressly
 * stated in the License.
 */

#include "ti960.h"
#include "ti960-reg.h"
#include "ti953.h"
#include "ipu-utils.h"

/*LDRA_INSPECTED 426 S */
/*LDRA_INSPECTED 68 S */
#undef LOG_TAG
#define LOG_TAG "SERDES"
int32_t ti953_reg_write(struct ti960 *ti, uint16_t rx_port,
		uint16_t ser_alias, uint16_t reg, uint32_t val)
{
	uint16_t backup_addr;
	int32_t ret;

	backup_addr = ti->i2c_cfg.i2c_slave_addr;
	ti->i2c_cfg.i2c_slave_addr = ser_alias;
	ret = ti960_reg_write(ti, reg, val);
	ti->i2c_cfg.i2c_slave_addr = backup_addr;

	return ret;
}

int32_t ti953_reg_read(struct ti960 *ti, uint16_t rx_port,
		uint16_t ser_alias, uint16_t reg, uint32_t *val)
{
	uint16_t backup_addr;
	int32_t ret;

	backup_addr = ti->i2c_cfg.i2c_slave_addr;
	ti->i2c_cfg.i2c_slave_addr = ser_alias;
	ret = ti960_reg_read(ti, reg, val);
	ti->i2c_cfg.i2c_slave_addr = backup_addr;

	return ret;
}

int32_t ti953_detect(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias)
{
	int32_t ret = 0;
	uint32_t i;
	uint32_t val;

	for (i = 0U; i < ARRAY_SIZE(ti953_FPD3_RX_ID); i++) {
		ret = ti953_reg_read(ti, rx_port, ser_alias, ti953_FPD3_RX_ID[i].reg, &val);
		if (ret != 0) {
			LOGW("rx_port %d, ti953 detect timeout %d", rx_port, ret);
			break;
		}

		if (val != ti953_FPD3_RX_ID[i].val_expected) {
			LOGE("detect failed expect %d actual %d",
					ti953_FPD3_RX_ID[i].val_expected, val);
			break;
		}
	}

	if (i == ARRAY_SIZE(ti953_FPD3_RX_ID)) {
		LOGI("TI953 0x%x detected", ser_alias);
		ret = 1;
	}

	return ret;
}

int32_t ti953_init(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias, uint8_t i2c_speed)
{
	struct ti953_register_write scl_high_reg;
	struct ti953_register_write scl_low_reg;
	int32_t ret;
	uint32_t i;

	for (i = 0U; i < ARRAY_SIZE(ti953_init_settings); i++) {
		ret = ti953_reg_write(ti, rx_port, ser_alias,
				ti953_init_settings[i].reg,
				ti953_init_settings[i].val);
		if (ret != 0) {
			LOGE("port %u, ti953 write timeout %d", rx_port, ret);
			break;
		}
	}

	for (i = 0U; i < ARRAY_SIZE(ti953_init_settings_clk); i++) {
		ret = ti953_reg_write(ti, rx_port, ser_alias,
				ti953_init_settings_clk[i].reg,
				ti953_init_settings_clk[i].val);
		if (ret != 0) {
			LOGE("port %u, ti953 write timeout %d", rx_port, ret);
			break;
		}
	}

	scl_high_reg.reg = TI953_SCL_HIGH_TIME;
	scl_low_reg.reg = TI953_SCL_LOW_TIME;
	switch (i2c_speed) {
	case TI953_I2C_SPEED_STANDARD:
		scl_high_reg.val = TI953_I2C_SCL_HIGH_TIME_STANDARD;
		scl_low_reg.val = TI953_I2C_SCL_LOW_TIME_STANDARD;
		break;
	case TI953_I2C_SPEED_FAST:
		scl_high_reg.val = TI953_I2C_SCL_HIGH_TIME_FAST;
		scl_low_reg.val = TI953_I2C_SCL_LOW_TIME_FAST;
		break;
	case TI953_I2C_SPEED_FAST_PLUS:
		scl_high_reg.val = TI953_I2C_SCL_HIGH_TIME_FAST_PLUS;
		scl_low_reg.val = TI953_I2C_SCL_LOW_TIME_FAST_PLUS;
		break;
	case TI953_I2C_SPEED_HIGH:
	default:
		LOGE("port %u, ti953 unsupported I2C speed mode %u", rx_port, i2c_speed);
		scl_high_reg.val = TI953_I2C_SCL_HIGH_TIME_STANDARD;
		scl_low_reg.val = TI953_I2C_SCL_LOW_TIME_STANDARD;
		ret = -EINVAL;
		break;
	}
	if (ret != 0) {
		return ret;
	}
	ret = ti953_reg_write(ti, rx_port, ser_alias, scl_high_reg.reg, scl_high_reg.val);
	if (ret != 0) {
		LOGE("port %u, ti953 write SCL_HIGH_TIME failed %d", rx_port, ret);
		return ret;
	}
	ret = ti953_reg_write(ti, rx_port, ser_alias, scl_low_reg.reg, scl_low_reg.val);
	if (ret != 0) {
		LOGE("port %u, ti953 write SCL_LOW_TIME failed %d", rx_port, ret);
		return ret;
	}

	return 0;
}

int32_t ti953_check_csi_payload(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias)
{
	int32_t ret = 0;
	uint32_t val[4] = {0U};

	if (ARRAY_SIZE(ti953_dbg_csi_payload) > 4U) {
		LOGE("rx_port %d, ti953 csi payload array size %d is bigger than 4",
				rx_port, ARRAY_SIZE(ti953_dbg_csi_payload));
		return -EINVAL;
	}

	for (uint8_t i = 0U; i < ARRAY_SIZE(ti953_dbg_csi_payload); i++) {
		ret = ti953_reg_read(ti, rx_port, ser_alias, ti953_dbg_csi_payload[i].reg, &val[i]);
		if (ret != 0) {
			LOGE("rx_port %d, ti953 csi payload reg 0x%x read failed %d", rx_port,
				 ti953_dbg_csi_payload[i].reg, ret);
			break;
		}
	}

	if (ret == 0) {
		LOGW("rx_port %d, ti953 csi payload vc-%u wc_lsb-%u wc_msb-%u ecc-%u",
				rx_port, val[0], val[1], val[2], val[3]);
	}

	return ret;
}

static void ti953_read_register_array(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias,
				const struct ti953_register_array *reg, const uint8_t size)
{
	uint16_t i, j;

	for (j = 0; j < size; j++) {
		for (i = 0U; i <= reg[j].size; i++) {
			uint32_t val;
			int32_t ret;

			ret = ti953_reg_read(ti, rx_port, ser_alias, reg[j].start_reg + i, &val);
			if (ret == 0) { /* Ignore write only register */
				LOGW("ti-%u rx_port %u, ti953 %s [0x%x 0x%x]", ti->cfg.id, rx_port,
					 reg[j].name, reg[j].start_reg + i, val);
			}
		}
	}
}

int32_t ti953_check_status(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias)
{
	int32_t ret = 0;
	uint32_t val = 0U;

	ti953_read_register_array(ti, rx_port, ser_alias,
							ti953_all, ARRAY_SIZE(ti953_all));
	ret = ti953_check_csi_payload(ti, rx_port, ser_alias);
	if (ret != 0) {
		return ret;
	}

	return ret;
}

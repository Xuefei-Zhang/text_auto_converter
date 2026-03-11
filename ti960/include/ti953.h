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

#ifndef TI953_H
#define TI953_H
#include "ti960.h"

struct ti953_register_write {
	uint8_t reg;
	uint8_t val;
};

struct ti953_register_devid {
	uint8_t reg;
	uint8_t val_expected;
};

struct ti953_register_array {
	char *name;
	uint16_t start_reg;
	uint8_t size;
};

/* register definition */
#define TI953_DEVICE_ID			0x0U
#define TI953_RESET_CTL			0x1U
#define TI953_GENERAL_CFG		0x2U
#define TI953_LOCAL_GPIO_DATA		0xdU
#define TI953_GPIO_INPUT_CTRL		0xeU
#define TI953_SCL_HIGH_TIME		0xbU
#define TI953_SCL_LOW_TIME		0xcU

/* register value definition */
#define TI953_DIGITAL_RESET_1		0x2U
#define TI953_GPIO0_RMTEN		0x10U
#define TI953_GPIO0_OUT			0x1U
#define TI953_GPIO1_OUT			(0x1U << 1U)
#define TI953_GPIO_OUT_EN		0xf0U
#define TI953_CONTS_CLK			0x40U
#define TI953_CSI_1LANE			0x00U
#define TI953_CSI_2LANE			0x10U
#define TI953_CSI_4LANE			0x30U
#define TI953_CRC_TX_GEN_ENABLE		0x2U
#define TI953_I2C_STRAP_MODE		0x1U
#define TI953_I2C_SCL_HIGH_TIME_STANDARD	0x7F
#define TI953_I2C_SCL_LOW_TIME_STANDARD		0x7F
#define TI953_I2C_SCL_HIGH_TIME_FAST		0x13
#define TI953_I2C_SCL_LOW_TIME_FAST		0x26
#define TI953_I2C_SCL_HIGH_TIME_FAST_PLUS	0x06
#define TI953_I2C_SCL_LOW_TIME_FAST_PLUS	0x0b
#define TI953_I2C_SPEED_STANDARD	0x1U
#define TI953_I2C_SPEED_FAST	0x2U
#define TI953_I2C_SPEED_HIGH	0x3U
#define TI953_I2C_SPEED_FAST_PLUS	0x4U

static const struct ti953_register_array ti953_all[] = {
	{"general register", 0x00, 0x1b},
	{"alarm register", 0x1c, 0x4},
	{"csi register", 0x20, 0x12},
	{"bcc+i2c register", 0x32, 0x1f},
	{"device status register", 0x51, 0x6},
	{"csi status register", 0x57, 0xe},
};

static const struct ti953_register_write ti953_init_settings[] = {
	{0x02, 0x73},
	{0x03, 0x10},
};

static const struct ti953_register_write ti953_init_settings_clk[] = {
	{0x06, 0x41},
	{0x07, 0x28},
};

static const struct ti953_register_write ti953_dbg_alarm_enable[] = {
};

static const struct ti953_register_devid ti953_FPD3_RX_ID[] = {
	{0xf0, 0x5f},
	{0xf1, 0x55},
	{0xf2, 0x42},
	{0xf3, 0x39},
	{0xf4, 0x35},
	{0xf5, 0x33},
};

static const struct ti953_register_devid ti953_dbg_csi_payload[] = {
	{0x61, 0x00}, /* csi vc id */
	{0x62, 0x00}, /* csi payload wc lsb */
	{0x63, 0x00}, /* csi payload wc msb */
	{0x64, 0x00}, /* csi ecc */
};

int32_t ti953_reg_write(struct ti960 *ti, uint16_t rx_port,
		uint16_t ser_alias, uint16_t reg, uint32_t val);

int32_t ti953_reg_read(struct ti960 *ti, uint16_t rx_port,
		uint16_t ser_alias, uint16_t reg, uint32_t *val);

int32_t ti953_detect(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias);

int32_t ti953_init(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias, uint8_t i2c_speed);

int32_t ti953_detect(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias);

int32_t ti953_check_status(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias);

int32_t ti953_check_csi_payload(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias);
#endif

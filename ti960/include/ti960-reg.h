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

#ifndef TI960_REG_H
#define TI960_REG_H

struct ti960_register_write {
	uint8_t reg;
	uint8_t val;
};

struct ti960_register_devid {
	uint8_t reg;
	uint8_t val_expected;
};

struct ti960_register_array {
	char *name;
	uint16_t start_reg;
	uint8_t size;
};

static const struct ti960_register_array ti960_general[] = {
	/* general check */
	{"general register", 0x00, 0x32},
};

static const struct ti960_register_array ti960_csi_tx[] = {
	/* csi check */
	{"csi-2", 0x33, 0x7},
	{"csi-2 debug", 0x90, 0x0f},
};

static const struct ti960_register_array ti960_rx_port_status[] = {
	/* rx port */
	{"Digital rx port", 0x46, 0x39},
	{"Digital rx port debug", 0xd0, 0x0f},
	{"FPD3 rx id", 0xf0, 0x05},
	{"Port i2c addressing", 0xf8, 0x03},
};

static const struct ti960_register_write ti960_frame_sync_settings[2][5] = {
	{
		{0x18, 0x00}, /* Disable frame sync. */
		{0x19, 0x00},
		{0x1a, 0x00},
		{0x1b, 0x00},
		{0x1c, 0x00},
	},
	{
		{0x19, 0x15}, /* Frame sync high time.*/
		{0x1a, 0xb3},
		{0x1b, 0xc3}, /* Frame sync low time. */
		{0x1c, 0x4f},
		{0x18, 0x01}, /* Enable frame sync. and use high/low mode */
	}
};

static const struct ti960_register_write ti960_gpio_settings[] = {
	{0x10, 0x81},
	{0x11, 0x85},
	{0x12, 0x89},
	{0x13, 0x8d},
};

static const struct ti960_register_write ti960_init_settings[] = {
	{0x0c, 0x0f}, /* RX_PORT_CTL */
	{0x1f, 0x06}, /* CSI_PLL_CTL */
	/* RX port0 Config */
	{0x4c, 0x01}, /* FPD3_PORT_SEL */
	{0x58, 0x5e}, /* BCC_CONFIG */
	{0x5c, 0xb0}, /* SER_ALIAS_ID */
	{0x5d, 0x6c}, /* SlaveID[0] */
	{0x65, 0x60}, /* SlaveAlias[0] */
	{0x6d, 0x7c}, /* PORT_CONFIG */
	{0x7c, 0x81}, /* PORT_CONFIG2 */
	{0x70, 0x1e}, /* RAW10_ID */
	{0x71, 0x2c}, /* RAW12_ID */
	{0x72, 0xe4}, /* CSI_VC_MAP */
	{0xd2, 0x1a},
	/* RX port1 Config */
	{0x4c, 0x12}, /* FPD3_PORT_SEL */
	{0x58, 0x5e},
	{0x5c, 0xb2},
	{0x5d, 0x6c},
	{0x65, 0x62},
	{0x6d, 0x7c},
	{0x7c, 0x81},
	{0x70, 0x1e},
	{0x71, 0x2c},
	{0x72, 0xe4}, /* CSI_VC_MAP */
	{0xd2, 0x1a},
	/* RX port2 Config */
	{0x4c, 0x24}, /* FPD3_PORT_SEL */
	{0x58, 0x5e},
	{0x5c, 0xb4},
	{0x5d, 0x6c},
	{0x65, 0x64},
	{0x6d, 0x7c},
	{0x7c, 0x81},
	{0x70, 0x1e},
	{0x71, 0x2c},
	{0x72, 0xe4},
	{0xd2, 0x1a},
	/* RX port2 Config */
	{0x4c, 0x38}, /* FPD3_PORT_SEL */
	{0x58, 0x5e},
	{0x5c, 0xb6},
	{0x5d, 0x6c},
	{0x65, 0x66},
	{0x6d, 0x7c},
	{0x7c, 0x81},
	{0x70, 0x1e},
	{0x71, 0x2c},
	{0x72, 0xe4},
	{0xd2, 0x1a},
	/* RX shared config */
	{0xb0, 0x14}, /* FPD3 RX Shared Reg */
	{0xb1, 0x03},
	{0xb2, 0x04},
	{0xb1, 0x04},
	{0xb2, 0x04},
	{0x20, 0xF0}, /* Disable forwarding on each RX port */
	{0x21, 0x03},
};


/* register definition */
#define TI960_DEVID		0x0U
#define TI960_RESET		0x1U
#define TI960_CSI_PLL_CTL	0x1fU
#define TI960_FS_CTL		0x18U
#define TI960_FWD_CTL1		0x20U
#define TI960_FWD_CTL2		0x21U
#define TI960_RX_PORT_SEL	0x4cU
#define TI960_SER_ALIAS_ID	0x5cU
#define TI960_SLAVE_ID0		0x5dU
#define TI960_SLAVE_ID1		0x5eU
#define TI960_SLAVE_ALIAS_ID0	0x65U
#define TI960_SLAVE_ALIAS_ID1	0x66U
#define TI960_PORT_CONFIG	0x6dU
#define TI960_BC_GPIO_CTL0	0x6eU
#define TI960_BC_GPIO_CTL1	0x6fU
#define TI960_RAW10_ID		0x70U
#define TI960_RAW12_ID		0x71U
#define TI960_CSI_VC_MAP	0x72U
#define TI960_PORT_CONFIG2	0x7cU
#define TI960_CSI_PORT_SEL	0x32U
#define TI960_CSI_CTL		0x33U
#define TI960_RX_PORT_STS1	0x4dU

/* register value definition */
#define TI960_POWER_ON		0x1U
#define TI960_POWER_OFF		0x20U
#define TI960_FPD3_RAW10_100MHz	0x7fU
#define TI960_FPD3_RAW12_50MHz	0x7dU
#define TI960_FPD3_RAW12_75MHz	0x7eU
#define TI960_FPD3_CSI		0x7cU
#define TI960_RAW12		0x41U
#define TI960_RAW10_NORMAL	0x1U
#define TI960_RAW10_8BIT	0x81U
#define TI960_GPIO0_HIGH	0x09U
#define TI960_GPIO0_LOW		0x08U
#define TI960_GPIO1_HIGH	0x90U
#define TI960_GPIO1_LOW		0x80U
#define TI960_GPIO0_FSIN	0x0aU /* 0b1010 framesync signal */
#define TI960_GPIO1_FSIN	0xa0U
#define TI960_GPIO0_MASK	0x0fU
#define TI960_GPIO1_MASK	0xf0U
#define TI960_GPIO2_FSIN	0x0aU
#define TI960_GPIO3_FSIN	0xa0U
#define TI960_GPIO2_MASK	0x0fU
#define TI960_GPIO3_MASK	0xf0U
#define TI960_MIPI_800MBPS	0x2U
#define TI960_MIPI_1600MBPS	0x0U
#define TI960_CSI_ENABLE	0x1U
#define TI960_CSI_CONTS_CLOCK	0x2U
#define TI960_CSI_SKEWCAL	0x40U
#define TI960_CSI_2LANE		0x20U
#define TI960_FSIN_ENABLE	0x1U
#define TI960_RR_FORWARD	0x03U /* Enable best-effort forwarding for CSI-2 output port0/1 */
#define TI960_SYNC_FORWARD	0x14U /* Enable synchronized forwarding for CSI-2 output port0/1 */
#define TI960_LOCKED		0x1U

/* register default value */
#define TI960_CSI_PLL_CTL_DEF	0x2U
#define TI960_CSI_CTL_DEF	0x0U

/* TI960 rx port status */
#define TI960_RX_STS_PORT_NUM(val)	((val >> 6U) & 0x3U)
#define TI960_RX_STS_CHG(val)	((val >> 4U) & 0x1U)
#define TI960_RX_STS_LOCKED(val)	(val & 0x1U)
#endif

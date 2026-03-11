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

#ifndef TI960_H
#define TI960_H

#include <stdint.h>
#include "io-aux.h"

#define TI960_NAME "ti960"

#define MAX_TI960_INSTANCE_SUPPORT	3U
#define TI960_MAX_SUBDEV_SUPPORT	8U
#define TI960_MAX_SENSOR_SUPPORT	4U

#define MAX_GPIO_POWERUP_SEQ    4U

#define CSF_TI960_FLAG_INIT_SER (1U << 0U)
#define CSF_TI960_FLAG_POWERUP (1U << 1U)
#define CSF_TI960_FLAG_RESET (1U << 2U)

#define TI960_LINK_FREQ_800MBPS 800U
#define TI960_LINK_FREQ_1200MBPS 1200U
#define TI960_LINK_FREQ_1600MBPS 1600U

enum ti960_subdev_type {
	TI960_SUBDEV_SENSOR = 0U,
	TI960_SUBDEV_EEPROM = 1U,
};

struct ti960_subdev_config {
	uint8_t port; /* CSI port */
	uint8_t rx_port; /* CSI port */
	uint8_t lanes;
	uint8_t phy_i2c_addr; /* I2C physical address */
	uint8_t alias_i2c_addr; /* I2C physical address */
	uint8_t ser_i2c_addr; /* I2C alias address on serializer */
	uint8_t ser_i2c_speed; /* I2C speed on serializer */
	uint32_t fsin_gpio;
	int32_t gpio_powerup_seq[MAX_GPIO_POWERUP_SEQ];
	uint32_t flags;
	uint8_t enabled; /* fpd link connection ready */
	uint32_t reset;
	uint32_t dev_type;
};

struct ti960_config {
	uint8_t id;

	uint8_t i2c_bus_id; /* TI960 I2C bus ID */
	uint8_t i2c_slave_address; /* TI960 I2c slave address */
	uint32_t reset_gpio;
	uint32_t fpd_link_gpio; /* Set high poweron fpd link */
	uint8_t subdev_num; /* connected subdev numbers */
	struct ti960_subdev_config subdev_info[TI960_MAX_SUBDEV_SUPPORT]; /* subdev info config */
	/**
	 * 00 : 1.472 - 1.664 Gbps serial rate
	 * 01 : 1.2 Gbps serial rate
	 * 10 : 800 Mbps serial rate
	 * 11 : 400 Mbps serial rate
	 */
	uint8_t link_freq;
	uint8_t lanes;
	uint8_t init_once;
	enum io_aux_i2c_speed_mode i2c_speed_mode;
};

struct ti960 {
	char name[32];

	int8_t enable_broadcast; /* enable broadcast mode */
	int8_t enable_broadcast_streaming; /* enable broadcast mode during streaming */
	uint8_t enable_sync; /* Flag whether enable serdes sync config or not */
	uint8_t initialized;
	struct ti960_config cfg;
	/* io_aux_i2c_cfg  with this */
	struct io_aux_i2c_config i2c_cfg;
};

/**
 * @brief TI960 driver initialization
 *
 * @return int32_t - 0 on success, others fail
 */
int32_t ti960_init(struct ti960_config *config);

/**
 * @brief ti960 i2c register write
 *
 * @param ti - pointer to ti960
 * @param reg - register offset
 * @param val - val to write
 * @return int32_t - 0 on success, others fail
 */
int32_t ti960_reg_write(struct ti960 *ti, uint16_t reg, uint32_t val);
/**
 * @brief ti960 i2c register read
 *
 * @param ti - pointer to ti960
 * @param reg - register offset
 * @param val - pointer to read val
 * @return int32_t - 0 on success, others fail
 */
int32_t ti960_reg_read(struct ti960 *ti, uint16_t reg, uint32_t *val);

struct ti960 *get_ti960(uint8_t id);

/**
 * @brief ti960 configure sensor i2c
 * set before sensor streamon,
 * map subdev sensor i2c address,
 * support broadcase or non-broadcast mode
 * @param ti - pointer to ti960
 * @param index - group lead sensor index
 * @param enable - 1 enable, 0 disable
 * @retuen int32_t - 0 on success, others fail
 */
int32_t ti960_set_stream_pre(struct ti960 *ti, uint32_t index, int32_t enable);

/**
 * @brief ti960 configure sensor i2c
 * set after sensor streamon.
 * configure frame sync + fsin config on broad cast
 * both need rx forward + reset sensor
 * support broadcase or non-broadcast mode
 * @param ti - pointer to ti960
 * @param enable - 1 enable, 0 disable
 * @retuen int32_t - 0 on success, others fail
 */
int32_t ti960_set_stream_post(struct ti960 *ti, int32_t enable);

/**
 * @brief ti960 register ti953-<index> isolatedly
 * Check FPD-III link + initialize ti953
 * bootup subdevice sensor
 * configure csr-rx
 * map subdevice phy + alias address
 *
 * @param ti - pointer to ti960
 * @param index - ti953-<index>
 * @return int32_t - 0 on success, others fail
 */
int32_t ti960_registered(struct ti960 *ti,  uint8_t index);
int32_t ti960_set_power(struct ti960 *ti, int32_t enable);
int32_t ti960_uninit(struct ti960 *ti);

int32_t ti960_check_status(struct ti960 *ti, uint32_t i);
#endif

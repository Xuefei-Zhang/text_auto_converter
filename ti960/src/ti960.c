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
#include "ipu-platform.h"

#ifndef TI960_I2C_ADDR
#define TI960_I2C_ADDR 0x3dU
#endif

/*LDRA_INSPECTED 426 S */
/*LDRA_INSPECTED 68 S */
#undef LOG_TAG
#define LOG_TAG "SERDES"
/*
 *  calling sequence
 *  1. power up
 *  set power
 *  csi port setup
 *  2. reset
 *  reset via gpio
 *  initialize setting
 *  3. registered
 *  map ser alias
 *  detect ser
 *  power up sensor if needed
 *  reset sensor if needed
 *  map detected sensors address
 *  4. set stream
 *  broadcast mode (same sensor and configuration)
 *  map sensor to the same alias
 *  stream on sensor
 *  enable frame sync
 *  enable gpio signal
 *  reset sensor if needed
 *  enable forwarding
 *  map sensors alias back
 *  non broadcast mode
 *  stream on sensor
 *  enable forwarding
 *  reset sensor if needed
 */
int32_t ti960_reg_write(struct ti960 *ti, uint16_t reg, uint32_t val)
{
	int32_t ret;
	uint8_t retries = 0U;

#ifdef SERDES_I2C_DEBUG
	LOGI("i2c-%u write addr: 0x%x, [0x%x, 0x%x]",
		 ti->i2c_cfg.i2c_bus_id, ti->i2c_cfg.i2c_slave_addr, reg, val);
#endif

	while (retries < 10U) {
		ret = io_aux_i2c_send(&ti->i2c_cfg, reg, val);
		if (ret == 0) {
			break;
		}

		LOGW("i2c write 0x%x failed(%d), retry %u", reg, ret, retries);
		retries++;
		ipu_sleep_usec(1000U);
	}

	if (ret != 0) {
		LOGE("i2c write 0x%x failed(%d)", reg, ret);
		return ret;
	}

	/* Delay 3ms for ti953 reset enable */
	if ((reg == TI953_RESET_CTL) && (val == TI953_DIGITAL_RESET_1) &&
		(ti->i2c_cfg.i2c_slave_addr != TI960_I2C_ADDR)) {
		/*
		 * Sleep 3ms for ti953 digital reset
		 */
		usleep(3000U);
	}
#ifdef SERDES_I2C_DEBUG
	uint32_t tmp_val = 0U;
	ret = io_aux_i2c_recv(&ti->i2c_cfg, reg, &tmp_val);
	if (ret != 0) {
		LOGW("i2c read failed reg(0x%x)", reg);
	}
	if (tmp_val != val) {
		LOGW("Warning i2c-%u write addr:0x%x [0x%x, 0x%x],expect: [0x%x, 0x%x]",
		ti->i2c_cfg.i2c_bus_id, ti->i2c_cfg.i2c_slave_addr, reg, tmp_val, reg, val);
	}
#endif
	return 0;
}

int32_t ti960_reg_read(struct ti960 *ti, uint16_t reg, uint32_t *val)
{
	int32_t ret;
	uint8_t retries = 0U;

	while (retries < 10U) {
		ret = io_aux_i2c_recv(&ti->i2c_cfg, reg, val);
		if (ret == 0) {
			break;
		}

		LOGW("i2c receive(reg: 0x%x) failed(%d), retry ", reg, ret, retries);
		ipu_sleep_usec(1000U);
		retries++;
	}

	if (ret != 0) {
		LOGE("i2c receive(reg: 0x%x) failed(%d)", reg, ret);
		return ret;
	}

#ifdef SERDES_I2C_DEBUG
	LOGI("i2c-%u read addr: 0x%x, [0x%x, 0x%x]",
		 ti->i2c_cfg.i2c_bus_id, ti->i2c_cfg.i2c_slave_addr, reg, *val);
#endif
	return 0;
}

static int32_t ti960_reg_set_bit(struct ti960 *ti, uint16_t reg, uint8_t bit, uint8_t val)
{
	uint32_t reg_val;
	int32_t ret;

	ret = ti960_reg_read(ti, reg, &reg_val);
	if (ret != 0) {
		/* read failed */
		return ret;
	}

	if (val != 0U) {
		reg_val |= 1U << bit;
	} else {
		reg_val &= ~(1U << bit);
	}

	return ti960_reg_write(ti, reg, reg_val);
}

static int32_t ti960_lock_check(struct ti960 *ti, uint16_t rx_port)
{
	int32_t ret = 0;
	uint32_t val;

	ret = ti960_reg_read(ti, TI960_RX_PORT_STS1, &val);
	if (ret != 0) {
		LOGE("read ti960 rx_port %d status failed(%d)", rx_port, ret);
		return ret;
	}

	if ((TI960_RX_STS_LOCKED(val) == TI960_LOCKED) &&
		(rx_port == TI960_RX_STS_PORT_NUM(val))) {
		LOGI("ti960 rx_port %d locked", rx_port);
	} else {
		LOGW("rx_port[%u] status 0x%x, port_num %u STS_CHG %u LOCK %u", rx_port, val,
		TI960_RX_STS_PORT_NUM(val), TI960_RX_STS_CHG(val), TI960_RX_STS_LOCKED(val));
		return -1;
	}

	return ret;
}

static int32_t ti960_fpd3_port_sel(struct ti960 *ti, uint16_t rx_port)
{
	int32_t ret = 0;

	ret = ti960_reg_write(ti, TI960_RX_PORT_SEL, (rx_port << 4U) + (1U << rx_port));
	if (ret != 0) {
		LOGE("ti960 select rx_port %u failed(%d)", rx_port, ret);
		return ret;
	}

	return ret;
}

static int32_t ti960_map_phy_i2c_addr(struct ti960 *ti, uint16_t rx_port, uint16_t addr, uint32_t dev_type)
{
	int32_t ret;

	ret = ti960_fpd3_port_sel(ti, rx_port);
	if (ret != 0) {
		LOGE("ti960 port(%d) selection failed(%d)", rx_port, ret);
		return ret;
	}
	if (dev_type == (uint32_t)TI960_SUBDEV_SENSOR) {
		ret = ti960_reg_write(ti, TI960_SLAVE_ID0, addr);
	} else if (dev_type == (uint32_t)TI960_SUBDEV_EEPROM) {
		ret = ti960_reg_write(ti, TI960_SLAVE_ID1, addr);
	} else {
		LOGE("ti960 port(%d) got not expected dev_type %u", rx_port, dev_type);
		return -EINVAL;
	}
	return ret;
}

static int32_t ti960_map_alias_i2c_addr(struct ti960 *ti, uint16_t rx_port, uint16_t addr, uint32_t dev_type)
{
	int32_t ret;

	ret = ti960_fpd3_port_sel(ti, rx_port);
	if (ret != 0) {
		LOGE("ti960 port(%d) selection failed(%d)", rx_port, ret);
		return ret;
	}

	if (dev_type == (uint32_t)TI960_SUBDEV_SENSOR) {
		ret = ti960_reg_write(ti, TI960_SLAVE_ALIAS_ID0, addr);
	} else if (dev_type == (uint32_t)TI960_SUBDEV_EEPROM) {
		ret = ti960_reg_write(ti, TI960_SLAVE_ALIAS_ID1, addr);
	} else {
		LOGE("ti960 port(%d) got not expected dev_type %u", rx_port, dev_type);
		return -EINVAL;
	}
	return ret;
}

static int32_t ti960_map_ser_alias_addr(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias)
{
	int32_t ret;

	ret = ti960_fpd3_port_sel(ti, rx_port);
	if (ret != 0) {
		LOGE("ti960 port(%d) selection failed(%d)", rx_port, ret);
		return ret;
	}

	return ti960_reg_write(ti, TI960_SER_ALIAS_ID, ser_alias);
}

static int32_t ti960_map_subdevs_addr(struct ti960 *ti, uint32_t i)
{
	uint16_t rx_port, phy_i2c_addr, alias_i2c_addr;
	int32_t ret;
	uint32_t dev_type;

	if (i >= TI960_MAX_SUBDEV_SUPPORT) {
		LOGE("ti960 subdev index(%d) is out of range(%d)", i, TI960_MAX_SUBDEV_SUPPORT);
		return -EINVAL;
	}

	rx_port = ti->cfg.subdev_info[i].rx_port;
	phy_i2c_addr = ti->cfg.subdev_info[i].phy_i2c_addr;
	alias_i2c_addr = ti->cfg.subdev_info[i].alias_i2c_addr;
	dev_type = ti->cfg.subdev_info[i].dev_type;
	if (ti->cfg.subdev_info[i].enabled == 0U && dev_type == (uint32_t)TI960_SUBDEV_SENSOR) {
		LOGE("%s subdev %u not enabled", __func__, i);
		return -EINVAL;
	}

	/* map PHY I2C address */
	ret = ti960_map_phy_i2c_addr(ti, rx_port, phy_i2c_addr, dev_type);
	if (ret != 0) {
		LOGE("map phy i2c address failed(%d)", ret);
		return ret;
	}

	/* set 7bit alias i2c addr */
	ret = ti960_map_alias_i2c_addr(ti, rx_port, alias_i2c_addr << 1, dev_type);
	if (ret != 0) {
		LOGE("map alias i2c address failed(%d)", ret);
		return ret;
	}

	return 0;
}

/*LDRA_INSPECTED 397 S */
static uint8_t ti960_config_once[MAX_TI960_INSTANCE_SUPPORT] = {};
static int32_t ti960_general_config(struct ti960 *ti)
{
	int32_t i, ret;

	if (ti960_config_once[ti->cfg.id] == 1U) {
		LOGW("Skip ti960-%u config", ti->cfg.id);
		return 0;
	}

	LOGI("ti960-%u config", ti->cfg.id);
	if (ti->cfg.init_once == 1U) {
		ti960_config_once[ti->cfg.id] = 1;
	}
	for (i = 0U; i < ARRAY_SIZE(ti960_gpio_settings); i++) {
		ret = ti960_reg_write(ti, ti960_gpio_settings[i].reg, ti960_gpio_settings[i].val);
		if (ret != 0) {
			LOGE("failed to write TI960 gpio setting, reg 0x%2x, val 0x%2x",
				ti960_gpio_settings[i].reg, ti960_gpio_settings[i].val);
			return ret;
		}
	}

	for (i = 0U; i < ARRAY_SIZE(ti960_init_settings); i++) {
		ret = ti960_reg_write(ti, ti960_init_settings[i].reg, ti960_init_settings[i].val);
		if (ret != 0) {
			LOGE("failed to write TI960 init setting, reg 0x%2x, val 0x%2x",
					ti960_init_settings[i].reg, ti960_init_settings[i].val);
			return ret;
		}
	}

	return 0;
}

static int32_t ti960_reset_init(struct ti960 *ti)
{
	uint32_t val, i;
	int32_t ret;
	uint32_t timeout = 30U; /* 3ms timeout*/

	if (ti960_config_once[ti->cfg.id] == 0U) {
		LOGI("ti960-%u gpio-%u reset", ti->cfg.id, ti->cfg.reset_gpio);
		/* HW reset */
		(void)gpio_set_value(ti->cfg.reset_gpio, 0);
		ipu_sleep_usec(2000U);
		(void)gpio_set_value(ti->cfg.reset_gpio, 1);
	} else {
		LOGD("skip ti960-%u gpio-%u reset", ti->cfg.id, ti->cfg.reset_gpio);
	}

#ifdef JETSON
	(void)gpio_request_and_init(ti->cfg.fpd_link_gpio);
	(void)gpio_set_value(ti->cfg.fpd_link_gpio, 1);
	LOGD("set gpio %d", ti->cfg.fpd_link_gpio);
	usleep(3000U);
#endif

	/* Digital reset */
	ret = ti960_set_power(ti, 1);
	if (ret != 0) {
		LOGE("ti960 power up failed(%d)", ret);
		return ret;
	}

	ret = ti960_reg_read(ti, TI960_DEVID, &val);
	while (ret != 0 && (timeout != 0U)) {
		ipu_sleep_usec(100U);
		ret = ti960_reg_read(ti, TI960_DEVID, &val);
		timeout--;
	}

	if (ret != 0) {
		LOGE("ti960 reset timeout %d", ret);
		return ret;
	} else {
		LOGD("ti960 reset check loop %u", (30U - timeout));
	}

	LOGI("TI960 device ID 0x%x", val);
	ret = ti960_general_config(ti);
	if (ret != 0) {
		LOGE("ti960 init config failed(%d)", ret);
		return ret;
	}

	return 0;
}


static int32_t ti960_csi_init(struct ti960 *ti, bool enable)
{
	int32_t ret;
	uint32_t val;

	/* CSI port0 selected per HW connection */
	ret = ti960_reg_write(ti, TI960_CSI_PORT_SEL, 0x1);
	if (ret != 0) {
		LOGE("ti960 write failed(%d)", ret);
		return ret;
	}

	val = enable ? ti->cfg.link_freq : TI960_CSI_PLL_CTL_DEF;
	/* Configure MIPI clock based on control value. */
	ret = ti960_reg_write(ti, TI960_CSI_PLL_CTL, val);
	if (ret != 0) {
		LOGE("ti960 write failed(%d)", ret);
		return ret;
	}

	if (enable) {
		val = TI960_CSI_ENABLE;
		val |= TI960_CSI_CONTS_CLOCK;
		if (ti->cfg.lanes == 2U) {
			val |= TI960_CSI_2LANE;
		}

		/* Enable skew calculation when 1.6Gbps output is enabled. */
		if (ti->cfg.link_freq == 0U) {
			val |= TI960_CSI_SKEWCAL;
			LOGI("ti960 deskew enabled");
		}
	} else {
		val = TI960_CSI_CTL_DEF;
	}

	LOGI("ti960 lane %d, link_freq 0x%x %s", ti->cfg.lanes, ti->cfg.link_freq,
		 enable ? "enable" : "disable");

	/* Reset CSI_CTL to avoid abnormal exit */
	ret = ti960_reg_write(ti, TI960_CSI_CTL, TI960_CSI_CTL_DEF);
	if (ret != 0) {
		LOGE("ti960 TI960_CSI_CTL reset failed(%d)", ret);
		return ret;
	}

	return ti960_reg_write(ti, TI960_CSI_CTL, val);
}

static int32_t ti960_fsin_gpio_init(struct ti960 *ti, uint16_t rx_port,
		uint16_t ser_alias, uint32_t fsin_gpio)
{
	uint32_t gpio_data;
	uint32_t reg_val;
	int32_t ret;

	ret = ti960_reg_read(ti, TI960_FS_CTL, &reg_val);
	if (ret != 0) {
		LOGE("failed to read gpio status(%d)", ret);
		return ret;
	}

	if ((reg_val & TI960_FSIN_ENABLE) == 0U) {
		LOGI("FSIN not enabled, skip config FSIN GPIO.");
		return 0;
	}

	ret = ti960_fpd3_port_sel(ti, rx_port);
	if (ret != 0) {
		LOGE("ti960 port selection failed(%d)", ret);
		return ret;
	}

	switch (fsin_gpio) {
	case 0U:
	case 1U:
		ret = ti960_reg_read(ti, TI960_BC_GPIO_CTL0, &reg_val);
		if (ret != 0) {
			LOGE("failed to read gpio status(%d)", ret);
			return ret;
		}

		if (fsin_gpio == 0U) {
			reg_val &= ~TI960_GPIO0_MASK;
			reg_val |= TI960_GPIO0_FSIN;
		} else {
			reg_val &= ~TI960_GPIO1_MASK;
			reg_val |= TI960_GPIO1_FSIN;
		}

		ret = ti960_reg_write(ti, TI960_BC_GPIO_CTL0, reg_val);
		if (ret != 0) {
			LOGE("failed to set gpio(%d)", ret);
			return ret;
		}
		break;
	case 2U:
	case 3U:
		ret = ti960_reg_read(ti, TI960_BC_GPIO_CTL1, &reg_val);
		if (ret != 0) {
			LOGE("failed to read gpio status(%d)", ret);
			return ret;
		}

		if (fsin_gpio == 2U) {
			reg_val &= ~TI960_GPIO2_MASK;
			reg_val |= TI960_GPIO2_FSIN;
		} else {
			reg_val &= ~TI960_GPIO3_MASK;
			reg_val |= TI960_GPIO3_FSIN;
		}

		ret = ti960_reg_write(ti, TI960_BC_GPIO_CTL1, reg_val);
		if (ret != 0) {
			LOGE("failed to set gpio(%d)", ret);
			return ret;
		}
		break;
	default:
		LOGE("invalid gpio number %d", fsin_gpio);
		break;
	}

	/* enable output and remote control */
	ret = ti953_reg_write(ti, rx_port, ser_alias, TI953_GPIO_INPUT_CTRL, TI953_GPIO_OUT_EN);
	if (ret != 0) {
		LOGE("ti953 write failed(%d)", ret);
		return ret;
	}

	ret = ti953_reg_read(ti, rx_port, ser_alias, TI953_LOCAL_GPIO_DATA, &gpio_data);
	if (ret != 0) {
		LOGE("ti953 read failed(%d)", ret);
		return ret;
	}

	ret = ti953_reg_write(ti, rx_port, ser_alias, TI953_LOCAL_GPIO_DATA,
			(gpio_data | (TI953_GPIO0_RMTEN << fsin_gpio)));
	if (ret != 0) {
		LOGE("ti953 write failed(%d)", ret);
		return ret;
	}

	return ret;
}

/*
 * FIXME: workaround, reset to avoid block.
 * Do we need this?
 */
static int32_t reset_sensor(struct ti960 *ti, uint16_t rx_port, uint16_t ser_alias, uint32_t reset)
{
	uint32_t gpio_data;
	int32_t ret;

	ret = ti953_reg_read(ti, rx_port, ser_alias, TI953_LOCAL_GPIO_DATA, &gpio_data);
	if (ret != 0) {
		LOGE("ti953 read failed(%d)", ret);
		return ret;
	}

	ret = ti953_reg_write(ti, rx_port, ser_alias, TI953_GPIO_INPUT_CTRL, TI953_GPIO_OUT_EN);
	if (ret != 0) {
		LOGE("ti953 write failed(%d)", ret);
		return ret;
	}
	gpio_data &= ~(TI953_GPIO0_RMTEN << reset);
	gpio_data &= ~(TI953_GPIO0_OUT << reset);
	ret = ti953_reg_write(ti, rx_port, ser_alias, TI953_LOCAL_GPIO_DATA, gpio_data);
	if (ret != 0) {
		LOGE("ti953 write failed(%d)", ret);
		return ret;
	}
	ipu_sleep_usec(50U * 1000U);
	gpio_data |= TI953_GPIO0_OUT << reset;
	ret = ti953_reg_write(ti, rx_port, ser_alias, TI953_LOCAL_GPIO_DATA, gpio_data);
	if (ret != 0) {
		LOGE("ti953 write failed(%d)", ret);
		return ret;
	}

	return 0;
}


/*LDRA_NOANALYSIS*/
/*LDRA_INSPECTED 397 S */
static uint8_t ti953_init_once[MAX_TI960_INSTANCE_SUPPORT][TI960_MAX_SENSOR_SUPPORT] = { {} };
int32_t ti960_registered(struct ti960 *ti, uint8_t index)
{
	int32_t i, j, k = 0, l, ret = 0;
	uint32_t m, val;
	uint32_t timeout = 200U; /* 20ms timeout*/

	FreeRTOSTrace("into ti960_registered");
	if (ti->initialized != 1U) {
		LOGE("ti960 init failed(%d)", ret);
		return ret;
	}

	if (i >= TI960_MAX_SUBDEV_SUPPORT) {
		LOGE("ti960 subdev index(%d) is out of range(%d)", i, TI960_MAX_SUBDEV_SUPPORT);
		return -EINVAL;
	}

	/* Check serializer hw connection situations */
	struct ti960_subdev_config *conf = &ti->cfg.subdev_info[index];

	if (conf->dev_type == (uint32_t)TI960_SUBDEV_SENSOR) {
		/* map serilaizer i2c addr, include rx-port selected */
		ret = ti960_map_ser_alias_addr(ti, conf->rx_port, conf->ser_i2c_addr << 1U);
		if (ret != 0) {
			LOGE("ti960 map ser alias addr(%d) failed(%d)", conf->ser_i2c_addr, ret);
			conf->enabled = 0U;
			return ret;
		}

		/* Wait for FPD Link III locked for incoming data */
		ret = ti960_lock_check(ti, conf->rx_port);
		while (ret != 0 && (timeout != 0U)) {
			/* sleep 100us per cycle for PnP optimization */
			ipu_sleep_usec(100U);
			ret = ti960_lock_check(ti, conf->rx_port);
			timeout--;
		}
		if (ret != 0) {
			LOGE("ti960 lock timeout %d", ret);
			return ret;
		} else {
			LOGI("lock check loop %u", (200U - timeout));
		}

		ret = ti953_detect(ti, conf->rx_port, conf->ser_i2c_addr);
		if (ret != 1) {
			LOGE("ti953 ser alias addr(%d) detect ID failed(%d)", conf->ser_i2c_addr, ret);
			conf->enabled = 0U;
			return ret;
		}

		conf->enabled = 1U; /* fpd link connected */

		/* ti953 init once */
		if (ti953_init_once[ti->cfg.id][conf->rx_port] == 0U) {
			if (ti->cfg.init_once == 1U) {
				ti953_init_once[ti->cfg.id][conf->rx_port] = 1U;
			}
			LOGW("ti960-%u, ti953-%u inited", ti->cfg.id, conf->rx_port);
			ret = ti953_reg_write(ti, conf->rx_port, conf->ser_i2c_addr,
					TI953_RESET_CTL, TI953_DIGITAL_RESET_1);
			if (ret != 0) {
				LOGE("ti953 write failed(%d)", ret);
				return ret;
			}

			/*
			 * ti953 pull down time is at least 3ms
			 * add 2ms more as buffer
			 */
			timeout = 50U;
			val = 0U;
			ret = ti953_reg_read(ti, conf->rx_port, conf->ser_i2c_addr, TI953_DEVICE_ID, &val);
			while ((ret != 0) && (timeout != 0U)) {
				/* sleep 100us per cycle for PnP optimization */
				ipu_sleep_usec(100U);
				ret = ti953_reg_read(ti, conf->rx_port, conf->ser_i2c_addr, TI953_DEVICE_ID, &val);
				if ((val == 0x30U) || (val == 0x32U)) {
					break;
				}
				timeout--;
			}
			if (timeout == 0U) {
				LOGE("ti953 pull down timeout");
			} else {
				LOGI("ti953 pull down succeed, loop time %d", (50 - timeout));
			}

			if ((conf->flags & CSF_TI960_FLAG_INIT_SER) != 0U) {
				ret = ti953_init(ti, conf->rx_port, conf->ser_i2c_addr, conf->ser_i2c_speed);
				if (ret != 0) {
					LOGE("ti953_init failed(%d)", ret);
					return ret;
				}
			}

			if ((conf->flags & CSF_TI960_FLAG_POWERUP) != 0U) {
				ret = ti953_reg_write(ti, conf->rx_port, conf->ser_i2c_addr,
						TI953_GPIO_INPUT_CTRL, TI953_GPIO_OUT_EN);
				if (ret != 0) {
					LOGE("ti953 write failed(%d)", ret);
					return ret;
				}
				/* boot sequence remote slave sensor */
				for (m = 0U; m < MAX_GPIO_POWERUP_SEQ; m++) {
					if (conf->gpio_powerup_seq[m] < 0) {
						break;
					}

					ret = ti953_reg_write(ti, conf->rx_port, conf->ser_i2c_addr,
							TI953_LOCAL_GPIO_DATA,
							(uint32_t)conf->gpio_powerup_seq[m]);
					if (ret != 0) {
						LOGE("ti953 write failed(%d)", ret);
						return ret;
					}
				}
			}
			/**
			 * I2C Strap Mode: I2C Voltage level
			 * CRC_TX_GEN_ENABLE: Transmitter CRC Generator
			 * CONTS_CLK:
			 * CSI-2 Clock Lane Configuration.
			 * 0 : Non Continuous Clock
			 * 1 : Continuous Clock
			 * CSI-2 Data lane configuration.
			 * 00: 1-lane configuration
			 * 01: 2-lane configuration
			 * 11: 4-lane configuration
			 */
			val = TI953_I2C_STRAP_MODE;
			val |= TI953_CRC_TX_GEN_ENABLE;

			if (ti->cfg.init_once == 0U) {
				val |= TI953_CONTS_CLK;
			}

			if (conf->lanes == 1U) {
				val |= TI953_CSI_1LANE;
			} else if (conf->lanes == 2U) {
				val |= TI953_CSI_2LANE;
			} else if (conf->lanes == 4U) {
				val |= TI953_CSI_4LANE;
			} else {
				LOGE("not expected ti953 csi lane %d", conf->lanes);
				return -EINVAL;
			}
			ret = ti953_reg_write(ti, conf->rx_port, conf->ser_i2c_addr, TI953_GENERAL_CFG, val);
			if (ret != 0) {
				LOGE("ti953 write failed(%d)", ret);
				return ret;
			}
		} else {
			LOGW("Skip ti960-%u, ti953-%u inited", ti->cfg.id, conf->rx_port);
		}
	}

	/* map subdev sensor i2c phy addr and alias addr */
	ret = ti960_map_subdevs_addr(ti, index);
	if (ret != 0U) {
		LOGE("map subdev address failed(%d)", ret);
		return ret;
	}

	LOGI("register index %u serilizer-%u", index, conf->rx_port);
	FreeRTOSTrace("exit ti960_registered");

	return 0;
}
/*LDRA_ANALYSIS*/

int32_t ti960_set_power(struct ti960 *ti, int32_t enable)
{
	int32_t ret;

	ret = ti960_reg_write(ti, TI960_RESET, (enable == 1) ? TI960_POWER_ON : TI960_POWER_OFF);
	if ((ret != 0) || (enable == 0)) {
		return ret;
	}

	return 0;
}

/*
 * sensor vc to ti960 vc mapping, pipe level configuration
 */
static int32_t ti960_rx_port_config(struct ti960 *ti, int32_t rx_port)
{
	struct ti960_subdev_config *conf = &ti->cfg.subdev_info[rx_port];
	uint32_t csi_vc_map;
	int32_t ret;
	int32_t i;

	/* Select RX port */
	ret = ti960_fpd3_port_sel(ti, (uint16_t)rx_port);
	if (ret != 0) {
		LOGE("failed to select RX port(%d)", ret);
		return ret;
	}

	ret = ti960_reg_write(ti, TI960_PORT_CONFIG, TI960_FPD3_CSI);
	if (ret != 0) {
		LOGE("failed to set port config(%d)", ret);
		return ret;
	}

	/*
	 * CSI VC MAPPING
	 * rx_port 0, VC-ID mapped to 0
	 * rx_port 1, VC-ID mapped to 1
	 * rx_port 2, VC-ID mapped to 2
	 * rx_port 3, VC-ID mapped to 3
	 */
	csi_vc_map = rx_port;
	LOGI("rx_port %d, csi_vc_map 0x%x", rx_port, csi_vc_map);
	ret = ti960_reg_write(ti, TI960_CSI_VC_MAP, csi_vc_map);
	if (ret != 0) {
		LOGE("failed to set port config(%d)", ret);
		return ret;
	}

	return 0;
}

/*
 * frame sync high time and low time is sensor specific
 */
static int32_t ti960_set_frame_sync(struct ti960 *ti, int32_t enable)
{
	/* Only enable sync when streamon and enable_sync is true */
	int32_t index = (int32_t)!!((ti->enable_sync != 0U) && (enable != 0));
	uint8_t reg, val;
	int32_t ret;
	uint32_t i;

	for (i = 0U; i < ARRAY_SIZE(ti960_frame_sync_settings[index]); i++) {
		reg = ti960_frame_sync_settings[index][i].reg;
		val = ti960_frame_sync_settings[index][i].val;
		ret = ti960_reg_write(ti, reg, val);
		if (ret != 0) {
			LOGE("failed to %s frame sync", (enable == 1) ? "enable" : "disable");
			return ret;
		}
	}

	return 0;
}

int32_t ti960_set_stream_pre(struct ti960 *ti, uint32_t index, int32_t enable)
{
	int32_t broadcast = ti->enable_broadcast;
	int32_t ret = 0;
	uint16_t rx_port;
	uint16_t alias_addr;
	uint8_t i, j;
	uint32_t dev_type;

	if (ti->initialized != 1U) {
		LOGE("ti960 not initialized yet");
		return -EINVAL;
	}

	if (index >= ti->cfg.subdev_num) {
		LOGE("Invalid index for serializer set stream pre");
		return -EINVAL;
	}

	if (broadcast != 0) {
		struct ti960_subdev_config *conf = &ti->cfg.subdev_info[index];

		/* Choose group lead sensor i2c address as broadcast alias address */
		alias_addr = conf->alias_i2c_addr;
		dev_type = conf->dev_type;
	}

	for (i = 0U; i < ti->cfg.subdev_num; i++) {
		struct ti960_subdev_config *conf = &ti->cfg.subdev_info[i];

		if ((conf->enabled == 0U) || (conf->dev_type != (uint32_t)TI960_SUBDEV_SENSOR)) {
			continue; /* Only handle enabled serilizer + sensor */
		}

		rx_port = conf->rx_port;
		LOGD("set_pre(%s)-<config> rx-%u", (conf->enabled == 1U) ? "true" : "false",
			 conf->rx_port);
		ret = ti960_rx_port_config(ti, (int32_t)rx_port);
		if (ret != 0) {
			LOGE("failed to config rx port(%d)", ret);
			return ret;
		}

		if (broadcast != 0) {
			if (i == index) {
				/* Do nothing */
			} else {
				ret = ti960_map_alias_i2c_addr(ti, rx_port, alias_addr << 1U, dev_type);
				if (ret != 0) {
					LOGE("failed to map alias(0x%x) %d", alias_addr, ret);
					return ret;
				}
			}
		}
	}

	return ret;
}

int32_t ti960_set_stream_post(struct ti960 *ti, int32_t enable)
{
	int32_t broadcast = ti->enable_broadcast;
	int32_t broadcast_streaming = ti->enable_broadcast_streaming;
	bool enable_sync = (ti->enable_sync != 0U) && (enable != 0);
	struct ti960_subdev_config *conf;
	uint16_t rx_port;
	uint8_t i;
	int32_t ret = 0;

	if (ti->initialized != 1U) {
		LOGE("ti960 not initialized yet");
		return -EINVAL;
	}

	if (broadcast == 0) {
		for (i = 0U; i < ti->cfg.subdev_num; i++) {
			conf = &ti->cfg.subdev_info[i];
			if ((conf->enabled == 0U) || (conf->dev_type != (uint32_t)TI960_SUBDEV_SENSOR)) {
				continue;
			}

			rx_port = conf->rx_port;
			/* RX port fordward */
			LOGD("set_post(%s)-<forward> rx>-%u", (enable == 1U) ? "enable" : "disable",
				 conf->rx_port);

			ret = ti960_reg_set_bit(ti, TI960_FWD_CTL1,
					rx_port + 4U, (uint8_t)(enable == 0));
			if (ret != 0) {
				LOGE("failed to forward RX port%d. enable %d", i, enable);
				return ret;
			}

			if ((conf->flags & CSF_TI960_FLAG_RESET) != 0U) {
				ret = reset_sensor(ti, rx_port, conf->ser_i2c_addr,
						conf->reset);
				if (ret != 0) {
					return ret;
				}
			}
		}
	} else {
		ret = ti960_set_frame_sync(ti, enable);
		if (ret != 0) {
			LOGE("failed to set frame sync(%d)", ret);
			return ret;
		}

		for (i = 0U; i < ti->cfg.subdev_num; i++) {
			conf = &ti->cfg.subdev_info[i];
			if (enable != 0 && conf->enabled != 0U) {
				if (conf->dev_type != (uint32_t)TI960_SUBDEV_SENSOR) {
					continue;
				}

				LOGD("set_post(%s)-<gpio init> index %u rx-%u",
					 (conf->enabled == 1U) ? "true" : "false", i, conf->rx_port);
				ret = ti960_fsin_gpio_init(ti, conf->rx_port, conf->ser_i2c_addr,
							conf->fsin_gpio);
				if (ret != 0) {
					LOGE("failed to enable frame sync gpio init(%d)", ret);
					return ret;
				}

				if ((conf->flags & CSF_TI960_FLAG_RESET) != 0U) {
					ret = reset_sensor(ti, conf->rx_port, conf->ser_i2c_addr,
							conf->reset);
					if (ret != 0) {
						LOGE("failed to reset sensor(%d)", ret);
						return ret;
					}
				}
			}
		}

		for (i = 0U; i < ti->cfg.subdev_num; i++) {
			conf = &ti->cfg.subdev_info[i];
			if ((conf->enabled == 0U) || (conf->dev_type != (uint32_t)TI960_SUBDEV_SENSOR)) {
				continue;
			}

			/* RX port fordward */
			rx_port = conf->rx_port;
			LOGD("set_post()-<forward> rx-%u", conf->rx_port);
			ret = ti960_reg_set_bit(ti, TI960_FWD_CTL1, rx_port + 4U, (uint8_t)(enable == 0));
			if (ret != 0) {
				LOGE("failed to forward RX port%d enable %d %d", i, enable, ret);
				return ret;
			}

			if (broadcast_streaming == 0) {
				/*
				 * Restore each subdev i2c address as we may
				 * touch it later.
				 */
				ret = ti960_map_subdevs_addr(ti, i);
				if (ret != 0) {
					LOGE("failed to map subdevs(%d)", ret);
					return ret;
				}
			}
		}

		/**
		 * Choose csi forward mode based on enable_sync
		 */
		ret = ti960_reg_write(ti, TI960_FWD_CTL2, enable_sync ? TI960_SYNC_FORWARD
							 : TI960_RR_FORWARD);
		if (ret != 0) {
			LOGE("failed to %s frame sync", enable_sync ? "enable" : "disable");
			return ret;
		}
	}

	return ret;
}

void bus_switch(struct ti960 *ti)
{
	uint16_t addr_backend = ti->i2c_cfg.i2c_slave_addr;

	ti->i2c_cfg.i2c_slave_addr = 0x70U;
	(void)ti960_reg_write(ti, 0x00, 0x01);
	ti->i2c_cfg.i2c_slave_addr = addr_backend;
}

static int32_t ti960_driver_init(struct ti960 *ti, struct ti960_config *config)
{
	int32_t ret;

	if ((ti == NULL) || (config == NULL)) {
		LOGE("null pointer error");
		return -ENOMEM;
	}

	(void)memcpy(&(ti->cfg), config, sizeof(struct ti960_config));
	(void)snprintf(ti->name, sizeof(ti->name), "%s", TI960_NAME);
	ti->i2c_cfg.i2c_bus_id = config->i2c_bus_id;
	ti->i2c_cfg.reg_bytes = 1U;
	ti->i2c_cfg.val_bytes = 1U;
	ti->i2c_cfg.i2c_slave_addr = config->i2c_slave_address;

	/* WA, hsd15016467858, revert back when issue fixed */
	ret = io_aux_i2c_init(ti->i2c_cfg.i2c_bus_id, config->i2c_speed_mode);
	if (ret != 0) {
		LOGE("i2c init failed(%d)", ret);
		return ret;
	}

	ti->enable_broadcast = 0; /* Disable broadcast by default */
#ifdef JETSON
	bus_switch(ti);
#endif

	ret = ti960_reset_init(ti);
	if (ret != 0) {
		LOGE("reset ti960 failed(%d)", ret);
		return ret;
	}

	ret = ti960_csi_init(ti, true);
	if (ret != 0) {
		LOGE("csi init failed(%d)", ret);
		return ret;
	}

	return 0;
}

/* global driver instane shared for all modules, initialized to be NULL */
static struct ti960 ti960_driver[MAX_TI960_INSTANCE_SUPPORT] = {};
struct ti960 *get_ti960(uint8_t id)
{
	if (id >= MAX_TI960_INSTANCE_SUPPORT) {
		return NULL;
	}

	return &ti960_driver[id];
}

int32_t ti960_init(struct ti960_config *config)
{
	struct ti960 *ti = get_ti960(config->id);
	uint32_t version;
	int32_t ret;

	FreeRTOSTrace("into ti960_init");
	if (ti == NULL) {
		LOGE("failed to get ti960");
		return -EINVAL;
	}

	if (ti->initialized == 1U) {
		LOGI("already initialized!");
		return 0;
	}

	(void)memset(ti, 0, sizeof(struct ti960));
	ret = ti960_driver_init(ti, config);
	if (ret != 0) {
		LOGE("ti960 driver init failed(%d)", ret);
		return ret;
	}

	ret = ti960_reg_read(ti, TI960_DEVID, &version);
	if (ret != 0) {
		LOGE("read ti960 device id failed(%d)", ret);
		return ret;
	}
	LOGI("%s device ID: 0x%x initialized", ti->name, version);
	ti->initialized = 1U; /* ti960 ready */
	FreeRTOSTrace("exit ti960_init");

	return 0;
}

int32_t ti960_uninit(struct ti960 *ti)
{
	if (ti->initialized == 0U) {
		LOGW("ti960-%u already uninitialized", ti->cfg.id);
		return 0;
	}

	if (ti->cfg.init_once == 1U) {
		int32_t ret;

		/* Disable csi-tx during streamoff */
		ret = ti960_csi_init(ti, false);
		if (ret != 0) {
			LOGE("csi init failed(%d)", ret);
			return ret;
		}
	}
	LOGI("ti960-%u uninit", ti->cfg.id);
	ti->initialized = 0U;

	return ti960_set_power(ti, 0);
}

static void ti960_read_register_array(struct ti960 *ti, uint32_t rx_port,
				const struct ti960_register_array *reg, const uint8_t size)
{
	uint16_t i, j;

	for (j = 0; j < size; j++) {
		for (i = 0U; i <= reg[j].size; i++) {
			uint32_t val;
			int32_t ret;

			ret = ti960_reg_read(ti, reg[j].start_reg + i, &val);
			if (ret == 0) { /* Ignore write only register */
				LOGW("ti-%u rx_port %d, ti960 %s [0x%x 0x%x]", ti->cfg.id, rx_port,
					 reg[j].name, reg[j].start_reg + i, val);
			}
		}
	}
}

int32_t ti960_check_status(struct ti960 *ti, uint32_t i)
{
	int32_t ret = 0;
	struct ti960_subdev_config *conf = &ti->cfg.subdev_info[i];

	if ((conf->enabled == 0U) || (conf->dev_type != (uint32_t)TI960_SUBDEV_SENSOR)) {
		return 0;
	}

	ret = ti953_check_status(ti, conf->rx_port, conf->ser_i2c_addr);
	if (ret != 0) {
		return ret;
	}

	ret = ti960_fpd3_port_sel(ti, conf->rx_port);
	if (ret != 0) {
		LOGE("ti960 port(%d) selection failed(%d)",
			 conf->rx_port, ret);
		return ret;
	}

	/* TI960 genral registers */
	ti960_read_register_array(ti, 0xff, ti960_general, ARRAY_SIZE(ti960_general));

	/* TI960 csi tx registers */
	ti960_read_register_array(ti, 0xff, ti960_csi_tx, ARRAY_SIZE(ti960_csi_tx));

	/*ti960 rx port specific registers */
	ti960_read_register_array(ti, conf->rx_port, ti960_rx_port_status,
			 ARRAY_SIZE(ti960_rx_port_status));

	return ret;
}


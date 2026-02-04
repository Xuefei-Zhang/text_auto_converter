# Vendor Configuration Converter Guide

This guide explains how to use the Python vendor configuration converter script to convert vendor's raw register format to both INI and TXT formats for sensor capture hardware configurations.

## Overview

The script converts vendor's raw register format to two formats used in sensor capture hardware debugging:

- **INI format**: Used for USB capture tools debugging (for uSenyun USB box with MAX9296)
- **TXT format**: Used for FreeRTOS development board debugging (ARM SOC board with I2C commands)

The vendor format is a raw register format with device addresses and register values, like the one in `refer/corrected_x8d+max96717+max9296.TXT`.

## Prerequisites

- Python 3.x installed on your system
- Input configuration file in vendor's raw register format

## Script Usage

### Basic Syntax

```bash
python vendor_converter.py --input vendor_config.txt --output_ini output.ini --output_txt output.txt
```

### Example

#### Convert vendor's raw register format to both INI and TXT:

```bash
python vendor_converter.py --input refer/corrected_x8d+max96717+max9296.TXT --output_ini output_config.ini --output_txt output_config.txt
```

## Format Specifications

### Vendor Format Structure
- Contains register operations in format `0xAAAA,0xDDDD` for writes or `0xAAAA` for reads
- Comments with device information like `# Device 1: Deserializer MAX9296 (7-bit Addr: 0x48)`
- Multiple devices with different I2C addresses in the same file

### INI Format Structure
- Uses `I2CADDR=` to specify I2C slave addresses
- Uses `REG= 0xAAAA,0xDDDD` for register writes (Address,Data)
- Uses `MODE= 16BITREG_BYTEWRITE` for register access mode
- Uses `DELAY= N` for delay commands
- Comments start with `#`

### TXT Format Structure
- Uses `i2cwrite bus slave_addr register_addr width data_width data` for register writes
- Uses `i2cread bus slave_addr register_addr width num_bytes` for register reads
- Comments start with `#`
- Format: `i2cwrite <bus> <slave_addr> <register_addr> <width> <data_width> <data>`

## Common Use Cases

### 1. Converting Vendor Configuration to USB Capture Format
When you have a vendor's raw register configuration and need to use it with USB capture tools:

```bash
python vendor_converter.py --input refer/corrected_x8d+max96717+max9296.TXT --output_ini usb_config.ini --output_txt dummy.txt
```

### 2. Converting Vendor Configuration to FreeRTOS Format
When you have a vendor's raw register configuration and need to deploy it on a FreeRTOS development board:

```bash
python vendor_converter.py --input refer/corrected_x8d+max96717+max9296.TXT --output_ini dummy.ini --output_txt freertos_config.txt
```

## Important Notes

- The script preserves register addresses and values during conversion
- Comments and device information are maintained where possible
- Device addresses are properly converted between 7-bit and 8-bit representations
- Always verify the converted configuration works in your target environment
- The script handles both single and multiple data value writes

## Troubleshooting

If the conversion doesn't work as expected:

1. Check that your input file follows the expected vendor format
2. Verify that register addresses and values are in the correct hexadecimal format (0x...)
3. Ensure there are no syntax errors in the input file
4. Make sure device addresses are properly specified in the comments

## Example Conversion

**Vendor Input:**
```
# Device 1: Deserializer MAX9296 (7-bit Addr: 0x48)
0x0002,0x63
```

**INI Output:**
```
# I2C Slave Address: 0x48 (Deserializer MAX9296)
I2CADDR= 0x90
MODE= 16BITREG_BYTEWRITE
REG= 0x0002,0x63
```

**TXT Output:**
```
i2cwrite 1 0x48 0x0002 2 1 0x63
```

All three represent the same register write operation: writing value 0x63 to register 0x0002 on I2C slave address 0x48.
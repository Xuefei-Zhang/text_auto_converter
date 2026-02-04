# Unified Sensor Configuration Converter Guide

This guide explains how to use the Python unified configuration converter script to convert between multiple formats for sensor capture hardware configurations.

## Overview

The script converts between multiple formats used in sensor capture hardware debugging:

- **Vendor Format**: Raw register format from vendor files (like corrected_x8d+max96717+max9296.TXT)
- **INI format**: Used for USB capture tools debugging (for uSenyun USB box with MAX9296)
- **TXT format**: Used for FreeRTOS development board debugging (ARM SOC board with I2C commands)

## Prerequisites

- Python 3.x installed on your system
- Input configuration file in any of the supported formats

## Script Usage

### Basic Syntax

```bash
python unified_converter.py --mode <conversion_mode> --input <input_file> --output <output_file>
```

### Conversion Modes

- `vendor_to_both`: Convert from vendor raw register format to both INI and TXT formats
- `ini_to_txt`: Convert from INI format to TXT format
- `txt_to_ini`: Convert from TXT format to INI format

### Examples

#### Convert vendor's raw register format to both INI and TXT:

```bash
python unified_converter.py --mode vendor_to_both --input refer/corrected_x8d+max96717+max9296.TXT --output_ini output_config.ini --output_txt output_config.txt
```

#### Convert INI to TXT format:

```bash
python unified_converter.py --mode ini_to_txt --input config.ini --output config.txt
```

#### Convert TXT to INI format:

```bash
python unified_converter.py --mode txt_to_ini --input config.txt --output config.ini
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

### 1. Converting Vendor Configuration to Both Formats
When you have a vendor's raw register configuration and need to use it with both USB capture tools and FreeRTOS development boards:

```bash
python unified_converter.py --mode vendor_to_both --input refer/corrected_x8d+max96717+max9296.TXT --output_ini usb_config.ini --output_txt freertos_config.txt
```

### 2. Converting Between INI and TXT Formats
When you need to convert between the two formats for different debugging environments:

```bash
# Convert INI to TXT
python unified_converter.py --mode ini_to_txt --input usb_config.ini --output freertos_config.txt

# Convert TXT to INI
python unified_converter.py --mode txt_to_ini --input freertos_config.txt --output usb_config.ini
```

## Important Notes

- The script preserves register addresses and values during conversion
- Comments and device information are maintained where possible
- Device addresses are properly converted between 7-bit and 8-bit representations
- Always verify the converted configuration works in your target environment
- The script handles both single and multiple data value writes

## Troubleshooting

If the conversion doesn't work as expected:

1. Check that your input file follows the expected format
2. Verify that register addresses and values are in the correct hexadecimal format (0x...)
3. Ensure there are no syntax errors in the input file
4. Make sure you're using the correct conversion mode
5. For vendor format, ensure device addresses are properly specified in the comments

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
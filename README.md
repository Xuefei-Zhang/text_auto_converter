# Sensor Configuration Converter Guide

This guide explains how to use the Python configuration converter script to convert between INI and TXT formats for sensor capture hardware configurations.

## Overview

The script converts between two formats used in sensor capture hardware debugging:

- **INI format**: Used for USB capture tools debugging
- **TXT format**: Used for FreeRTOS development board debugging

Both formats contain the same register values but use different syntax structures.

## Prerequisites

- Python 3.x installed on your system
- Input configuration files in either INI or TXT format

## Script Usage

### Basic Syntax

```bash
python config_converter.py --mode <conversion_mode> --input <input_file> --output <output_file>
```

### Conversion Modes

- `ini_to_txt`: Convert from INI format to TXT format
- `txt_to_ini`: Convert from TXT format to INI format

### Examples

#### Convert INI to TXT format:

```bash
python config_converter.py --mode ini_to_txt --input config.ini --output config.txt
```

#### Convert TXT to INI format:

```bash
python config_converter.py --mode txt_to_ini --input config.txt --output config.ini
```

## Format Specifications

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

### 1. Converting USB Capture Config to FreeRTOS Format
When you have a working configuration in INI format from USB capture tools and need to deploy it on a FreeRTOS development board:

```bash
python config_converter.py --mode ini_to_txt --input usb_config.ini --output freertos_config.txt
```

### 2. Converting FreeRTOS Config to USB Capture Format
When you've debugged and finalized a configuration on the FreeRTOS board and want to use it with USB capture tools:

```bash
python config_converter.py --mode txt_to_ini --input freertos_config.txt --output usb_config.ini
```

## Important Notes

- The script preserves register addresses and values during conversion
- Comments and documentation are maintained where possible
- Delay commands are converted to comments in the target format
- Always verify the converted configuration works in your target environment
- The script handles both single and multiple data value writes

## Troubleshooting

If the conversion doesn't work as expected:

1. Check that your input file follows the expected format
2. Verify that register addresses and values are in the correct hexadecimal format (0x...)
3. Ensure there are no syntax errors in the input file
4. Make sure you're using the correct conversion mode

## Example Conversion

**INI Input:**
```
I2CADDR= 0x6C
MODE= 16BITREG_BYTEWRITE
REG= 0x0100,0x01
```

**TXT Output:**
```
i2cwrite 1 0x6C 0x0100 2 1 0x01
```

Both represent the same register write operation: writing value 0x01 to register 0x0100 on I2C slave address 0x6C.
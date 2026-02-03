#!/usr/bin/env python3
"""
Configuration Converter Script for Sensor Capture Hardware

This script converts between:
- INI format (for USB capture tools debugging)
- TXT format (for FreeRTOS development board debugging)

Usage:
    python config_converter.py --mode ini_to_txt --input input.ini --output output.txt
    python config_converter.py --mode txt_to_ini --input input.txt --output output.ini
"""

import argparse
import re
import sys


def parse_i2c_command(command_str):
    """
    Parse an I2C command string and extract bus, slave address, register address, width, and data

    Args:
        command_str (str): The command string to parse

    Returns:
        tuple: (command_type, bus, slave_addr, reg_addr, width, data_list)
    """
    # Handle i2cread command
    read_match = re.match(r'i2cread\s+(\d+)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(\d+)\s+(\d+)', command_str.strip())
    if read_match:
        bus = int(read_match.group(1))
        slave_addr = read_match.group(2)
        reg_addr = read_match.group(3)
        width = int(read_match.group(4))
        num_bytes = int(read_match.group(5))
        return 'read', bus, slave_addr, reg_addr, width, [num_bytes]

    # Handle i2cwrite command with multiple data values
    write_match = re.match(r'i2cwrite\s+(\d+)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(\d+)\s+(\d+)\s+(.+)', command_str.strip())
    if write_match:
        bus = int(write_match.group(1))
        slave_addr = write_match.group(2)
        reg_addr = write_match.group(3)
        width = int(write_match.group(4))
        data_width = int(write_match.group(5))  # This is usually 1 or 2 for data width
        data_part = write_match.group(6).strip()

        # Parse the data values (could be multiple)
        data_values = []
        for val in data_part.split():
            val = val.strip()
            if val.startswith('0x'):
                data_values.append(int(val, 16))
            else:
                data_values.append(int(val))

        return 'write', bus, slave_addr, reg_addr, width, data_values

    # Alternative i2cwrite format (without explicit data width)
    alt_write_match = re.match(r'i2cwrite\s+(\d+)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(\d+)\s+(.+)', command_str.strip())
    if alt_write_match:
        bus = int(alt_write_match.group(1))
        slave_addr = alt_write_match.group(2)
        reg_addr = alt_write_match.group(3)
        width = int(alt_write_match.group(4))
        data_part = alt_write_match.group(5).strip()

        # Parse the data values (could be multiple)
        data_values = []
        for val in data_part.split():
            val = val.strip()
            if val.startswith('0x'):
                data_values.append(int(val, 16))
            else:
                data_values.append(int(val))

        return 'write', bus, slave_addr, reg_addr, width, data_values

    # Handle alternative i2cread format (without explicit width)
    alt_read_match = re.match(r'i2cread\s+(\d+)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(\d+)', command_str.strip())
    if alt_read_match:
        bus = int(alt_read_match.group(1))
        slave_addr = alt_read_match.group(2)
        reg_addr = alt_read_match.group(3)
        num_bytes = int(alt_read_match.group(4))
        # For read commands, we typically use width=2 for register address
        return 'read', bus, slave_addr, reg_addr, 2, [num_bytes]

    return None, None, None, None, None, []


def convert_txt_to_ini(txt_content):
    """
    Convert TXT format to INI format

    Args:
        txt_content (str): Content in TXT format

    Returns:
        str: Content in INI format
    """
    lines = txt_content.split('\n')
    ini_lines = []
    current_slave_addr = None
    current_operation_mode = None  # Track if we're in read or write mode
    current_bus = 1  # Default bus

    # Add header
    ini_lines.append('#')
    ini_lines.append('# *************************************************************************')
    ini_lines.append('#                       Configuration for Sensing USB Card')
    ini_lines.append('#                Converted from FreeRTOS format')
    ini_lines.append('# *************************************************************************')
    ini_lines.append('#')

    for line in lines:
        line = line.rstrip()  # Remove trailing whitespace

        # Skip empty lines
        if not line.strip():
            ini_lines.append('')
            continue

        # Handle comments
        if line.startswith('#'):
            # Convert FreeRTOS-style comments to INI-style
            # Skip comments that are just reading instructions
            if 'Reading from register' in line:
                continue
            # Skip the I2C Slave Address comments that were added during conversion
            if 'I2C Slave Address:' in line:
                continue
            converted_comment = line  # Keep the comment as is
            ini_lines.append(converted_comment)
            continue

        # Parse I2C commands
        cmd_type, bus, slave_addr, reg_addr, width, data_values = parse_i2c_command(line)

        if cmd_type == 'read':
            # For read commands, we need to handle them differently
            # Update slave address if it changed OR if we were previously in write mode
            if slave_addr != current_slave_addr or current_operation_mode == 'write':
                current_slave_addr = slave_addr
                current_operation_mode = 'read'
                ini_lines.append('')
                ini_lines.append(f'# I2C Slave Address: {slave_addr}')
                # Convert 7-bit address to 8-bit address (shift left by 1, no R/W bit distinction)
                slave_addr_7bit_int = int(slave_addr, 16)
                slave_addr_8bit = hex(slave_addr_7bit_int << 1)  # Shift left by 1, keep LSB as 0
                ini_lines.append(f'I2CADDR= {slave_addr_8bit}')
                ini_lines.append('MODE= 16BITREG_BYTEREAD')  # Set mode for reading
            elif current_operation_mode != 'read':
                # Switch to read mode if we weren't already in read mode
                current_operation_mode = 'read'
                ini_lines.append('MODE= 16BITREG_BYTEREAD')  # Set mode for reading

            # Add register addresses for reading (without data values)
            reg_hex = reg_addr[2:]  # Remove '0x' prefix
            ini_lines.append(f'REG= 0x{reg_hex}')
        elif cmd_type == 'write':
            # Update slave address if it changed OR if we were previously in read mode
            if slave_addr != current_slave_addr or current_operation_mode == 'read':
                current_slave_addr = slave_addr
                current_operation_mode = 'write'
                ini_lines.append('')
                ini_lines.append(f'# I2C Slave Address: {slave_addr}')
                # Convert 7-bit address to 8-bit address (shift left by 1, keep R/W bit as 0 for write)
                slave_addr_7bit_int = int(slave_addr, 16)
                slave_addr_8bit = hex(slave_addr_7bit_int << 1)  # Keep LSB as 0 for write
                ini_lines.append(f'I2CADDR= {slave_addr_8bit}')
                ini_lines.append('MODE= 16BITREG_BYTEWRITE')  # Set mode for writing
            elif current_operation_mode != 'write':
                # Switch to write mode if we weren't already in write mode
                current_operation_mode = 'write'
                ini_lines.append('MODE= 16BITREG_BYTEWRITE')  # Set mode for writing

            # Add register writes
            for i, data_val in enumerate(data_values):
                if i == 0:
                    # First data value goes with the register
                    reg_hex = reg_addr[2:]  # Remove '0x' prefix
                    data_hex = f"{data_val:02x}" if data_val < 256 else f"{data_val:04x}"
                    ini_lines.append(f'REG= 0x{reg_hex},0x{data_hex}')
                else:
                    # Additional values - increment register address
                    reg_int = int(reg_addr, 16) + i
                    reg_hex = f"{reg_int:04x}"
                    data_hex = f"{data_val:02x}" if data_val < 256 else f"{data_val:04x}"
                    ini_lines.append(f'REG= 0x{reg_hex},0x{data_hex}')
        else:
            # If it's not an I2C command, just add it as is (probably a comment or delay)
            if 'DELAY=' in line.upper():
                # Extract delay value and convert to INI format
                delay_match = re.search(r'DELAY=\s*(\d+)', line)
                if delay_match:
                    delay_val = delay_match.group(1)
                    ini_lines.append(f'DELAY= {delay_val}')
            elif line.strip():
                # Add non-I2C lines as comments
                ini_lines.append(f'# {line.strip()}')

    return '\n'.join(ini_lines)


def convert_ini_to_txt(ini_content):
    """
    Convert INI format to TXT format

    Args:
        ini_content (str): Content in INI format

    Returns:
        str: Content in TXT format
    """
    lines = ini_content.split('\n')
    txt_lines = []
    current_slave_addr = None  # Will be set when we encounter I2CADDR
    current_bus = 1  # Default bus

    # Add header
    txt_lines.append('# *************************************************************************')
    txt_lines.append('#                       FreeRTOS I2C Commands for Sensing USB Card')
    txt_lines.append('#                Converted from INI format')
    txt_lines.append('# *************************************************************************')
    txt_lines.append('')

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            txt_lines.append('')
            continue

        # Handle comments (starting with # or ;)
        if line.startswith('#') or line.startswith(';'):
            # Convert INI-style comments to FreeRTOS-style
            comment = line[1:].strip()  # Remove the # or ;
            if comment:  # Only add if there's actual comment text
                # Skip comments that are just headers or formatting
                if 'Configuration for Sensing USB Card' in comment and 'Converted from FreeRTOS format' in comment:
                    continue  # Skip the header that was added during reverse conversion
                txt_lines.append(f'# {comment}')
            else:
                txt_lines.append('#')
            continue

        # Handle I2CADDR directive
        addr_match = re.match(r'I2CADDR=\s*(0x[0-9a-fA-F]+)', line)
        if addr_match:
            # Convert 8-bit address back to 7-bit address (shift right by 1 to remove R/W bit)
            addr_8bit = addr_match.group(1)
            addr_8bit_int = int(addr_8bit, 16)
            addr_7bit = hex(addr_8bit_int >> 1)  # Shift right by 1 to remove R/W bit
            current_slave_addr = addr_7bit
            continue  # Don't add this to the output, we'll track it internally

        # Handle MODE directive
        if 'MODE=' in line.upper():
            # Just skip this line as it's not needed in TXT format
            continue

        # Handle REG directive for both write and read modes
        reg_match = re.match(r'REG=\s*(0x[0-9a-fA-F]+)(?:\s*,\s*(0x[0-9a-fA-F]+))?', line)
        if reg_match:
            reg_addr = reg_match.group(1)
            data_val = reg_match.group(2)  # This could be None if it's a read register

            if data_val is not None:
                # This is a write command (has data value)
                # Convert to i2cwrite command
                # Format: i2cwrite bus slave_addr reg_addr width data_width data_value
                # Using width=2 for register address and data_width=1 for data value
                if current_slave_addr:
                    # Use the converted 7-bit slave address
                    txt_lines.append(f'i2cwrite {current_bus} {current_slave_addr} {reg_addr} 2 1 {data_val}')
                else:
                    # If no slave address has been set yet, use a default (7-bit)
                    txt_lines.append(f'i2cwrite {current_bus} 0x36 {reg_addr} 2 1 {data_val}')  # 0x6C >> 1 = 0x36
            else:
                # This is a read command (no data value)
                # Convert to i2cread command
                # Format: i2cread bus slave_addr reg_addr width num_bytes
                # Using width=2 for register address and assuming 1 byte for num_bytes
                if current_slave_addr:
                    # Use the converted 7-bit slave address
                    # Determine number of bytes to read based on context or default to 1
                    txt_lines.append(f'i2cread {current_bus} {current_slave_addr} {reg_addr} 2 1')
                else:
                    # If no slave address has been set yet, use a default (7-bit)
                    txt_lines.append(f'i2cread {current_bus} 0x36 {reg_addr} 2 1')  # 0x6C >> 1 = 0x36
            continue

        # Handle DELAY directive
        delay_match = re.match(r'DELAY=\s*(\d+)', line, re.IGNORECASE)
        if delay_match:
            delay_ms = delay_match.group(1)
            txt_lines.append(f'# DELAY= {delay_ms}ms')
            continue

    return '\n'.join(txt_lines)


def main():
    parser = argparse.ArgumentParser(description='Convert between INI and TXT configuration formats')
    parser.add_argument('--mode', choices=['ini_to_txt', 'txt_to_ini'], required=True,
                        help='Conversion direction: ini_to_txt or txt_to_ini')
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--output', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    # Read input file
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            input_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Perform conversion
    if args.mode == 'ini_to_txt':
        output_content = convert_ini_to_txt(input_content)
    elif args.mode == 'txt_to_ini':
        output_content = convert_txt_to_ini(input_content)
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)
    
    # Write output file
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"Successfully converted {args.input} to {args.output}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
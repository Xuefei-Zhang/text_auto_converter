#!/usr/bin/env python3
"""
Unified Configuration Converter Script for Sensor Capture Hardware

This script converts between multiple formats:
- Vendor's raw register format (from vendor files like corrected_x8d+max96717+max9296.TXT)
- INI format (for USB capture tools debugging)
- TXT format (for FreeRTOS development board debugging)

Usage:
    # Convert vendor format to both INI and TXT:
    python unified_converter.py --mode vendor_to_both --input vendor_config.txt --output_ini output.ini --output_txt output.txt
    
    # Convert INI to TXT:
    python unified_converter.py --mode ini_to_txt --input input.ini --output output.txt
    
    # Convert TXT to INI:
    python unified_converter.py --mode txt_to_ini --input input.txt --output output.ini
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


def parse_vendor_config(content):
    """
    Parse the vendor's raw configuration format

    Args:
        content (str): Raw vendor configuration content

    Returns:
        list: List of parsed register operations with device info
    """
    lines = content.split('\n')
    operations = []

    current_device_info = {
        'name': 'Unknown',
        'addr': '0x00',
        'addr_8bit': '0x00',  # 8-bit address for INI format
        'comments': []
    }

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Handle delay commands in vendor format FIRST, before treating as comment
        # Look for delay-like comments that might indicate a delay
        if line.startswith('#') and ('delay' in line.lower() or 'wait' in line.lower()):
            # Add delay as a special operation
            delay_val = extract_delay_value(line)
            # If no numeric value found in the comment, use a default of 10ms
            if delay_val == 10 and ('delay here' in line.lower() or 'had delay' in line.lower()):
                # Common pattern indicating a standard delay was in original config
                delay_val = 10  # Default to 10ms for this pattern
            operations.append({
                'device': current_device_info.copy(),
                'delay': True,
                'delay_value': delay_val,
                'op_type': 'delay'
            })
            continue

        # Handle comments
        if line.startswith('#'):
            # Look for device information in comments
            # Handle original vendor format: # Device 1: Deserializer MAX9296 (7-bit Addr: 0x48)
            if 'Device' in line:
                # Extract device name and address from comment
                device_match = re.search(r'Device \d+: ([^(]+) \([^)]+Addr: (0x[0-9a-fA-F]+)\)', line)
                if device_match:
                    current_device_info['name'] = device_match.group(1).strip()
                    current_device_info['addr'] = device_match.group(2)
                    # Convert 7-bit address to 8-bit for INI format
                    addr_7bit_int = int(current_device_info['addr'], 16)
                    addr_8bit = hex(addr_7bit_int << 1)
                    current_device_info['addr_8bit'] = addr_8bit
            # Handle alternative format: #max9296 0x90 or #max96717 0x84
            elif 'max9296' in line.lower() or 'max96717' in line.lower() or 'ox08d10' in line.lower() or 'ox03c' in line.lower():
                # Try to extract address from alternative format
                alt_device_match = re.search(r'(max9296|max96717|ox08d10|ox03c|ox\d+d\d+?)\s+(0x[0-9a-fA-F]+)', line.replace(':', ' '), re.IGNORECASE)
                if alt_device_match:
                    device_name = alt_device_match.group(1).upper()
                    addr = alt_device_match.group(2)
                    # In this format, the address in the comment is often the target 8-bit address
                    # So we'll use it directly as the 8-bit address and calculate the 7-bit address
                    current_device_info['name'] = device_name
                    addr_8bit_int = int(addr, 16)
                    addr_7bit = hex(addr_8bit_int >> 1)  # Shift right to get 7-bit address
                    current_device_info['addr'] = addr_7bit
                    current_device_info['addr_8bit'] = addr  # Use the provided address as 8-bit
                else:
                    # Try simpler pattern: look for max9296 or similar followed by address
                    simple_match = re.search(r'(max9296|max96717|ox08d10|ox03c|ox\d+d\d+?)\W+(0x[0-9a-fA-F]+)', line, re.IGNORECASE)
                    if simple_match:
                        device_name = simple_match.group(1).upper()
                        addr = simple_match.group(2)
                        # This might be a 7-bit address that needs to be converted to 8-bit
                        # Or it might already be an 8-bit address - we'll assume it's 7-bit and convert to 8-bit
                        addr_7bit_int = int(addr, 16)
                        # Check if the address is in the typical 7-bit range (0x08-0x77)
                        if addr_7bit_int >= 0x08 and addr_7bit_int <= 0x77:
                            # Likely a 7-bit address, convert to 8-bit
                            addr_8bit = hex(addr_7bit_int << 1)
                            current_device_info['name'] = device_name
                            current_device_info['addr'] = addr
                            current_device_info['addr_8bit'] = addr_8bit
                        else:
                            # Likely already an 8-bit address, use as is
                            current_device_info['name'] = device_name
                            addr_8bit_int = int(addr, 16)
                            addr_7bit = hex(addr_8bit_int >> 1)  # Calculate 7-bit from 8-bit
                            current_device_info['addr'] = addr_7bit
                            current_device_info['addr_8bit'] = addr
            current_device_info['comments'].append(line)
            continue

        # Handle register operations in format: 0xAAAA,0xDDDD
        reg_match = re.match(r'(0x[0-9a-fA-F]+),(0x[0-9a-fA-F]+)', line)
        if reg_match:
            reg_addr = reg_match.group(1)
            reg_data = reg_match.group(2)

            # Add the operation with current device info
            operations.append({
                'device': current_device_info.copy(),
                'reg_addr': reg_addr,
                'reg_data': reg_data,
                'op_type': 'write'
            })

            # Reset comments for next operation
            current_device_info['comments'] = []
            continue

        # Handle register operations without data (reads) in format: 0xAAAA
        read_match = re.match(r'(0x[0-9a-fA-F]+)', line)
        if read_match and len(line) == 6:  # Length of '0xAAAA'
            reg_addr = read_match.group(1)

            # Add the operation with current device info
            operations.append({
                'device': current_device_info.copy(),
                'reg_addr': reg_addr,
                'reg_data': None,
                'op_type': 'read'
            })

            # Reset comments for next operation
            current_device_info['comments'] = []
            continue

    return operations


def extract_delay_value(line):
    """
    Extract delay value from a line that might contain delay information

    Args:
        line (str): Line that might contain delay information

    Returns:
        int: Delay value in milliseconds, default 10 if not found
    """
    # Look for patterns like "delay 10ms", "wait 5", "delay=10", etc.
    # Case-insensitive search for delay followed by a number
    patterns = [
        r'delay[=:.\s]*(\d+)',      # delay=10, delay 10, delay:10
        r'wait[=:.\s]*(\d+)',       # wait=5, wait 5
        r'(\d+)\s*ms',              # 10ms
        r'(\d+)\s*msec',            # 10msec
        r'(\d+)'                    # just a number in a delay context
    ]

    for pattern in patterns:
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue

    return 10  # default delay


def convert_vendor_to_ini(vendor_operations):
    """
    Convert vendor's raw register format to INI format

    Args:
        vendor_operations (list): List of parsed register operations

    Returns:
        str: Content in INI format
    """
    ini_lines = []

    # Add header
    ini_lines.append('#')
    ini_lines.append('# *************************************************************************')
    ini_lines.append('#                       Configuration for Sensing USB Card')
    ini_lines.append('#                Converted from Vendor Format')
    ini_lines.append('# *************************************************************************')
    ini_lines.append('#')

    current_slave_addr = None

    for op in vendor_operations:
        # Handle delay operations
        if op.get('op_type') == 'delay':
            ini_lines.append(f"DELAY= {op['delay_value']}")
            continue

        # Add any comments associated with this operation
        for comment in op['device']['comments']:
            ini_lines.append(comment)

        # Check if we need to switch to a new slave address
        if current_slave_addr != op['device']['addr_8bit']:
            current_slave_addr = op['device']['addr_8bit']
            ini_lines.append('')
            ini_lines.append(f"# I2C Slave Address: {op['device']['addr']} ({op['device']['name']})")
            ini_lines.append(f"I2CADDR= {op['device']['addr_8bit']}")

            # Set mode based on operation type
            if op['op_type'] == 'read':
                ini_lines.append('MODE= 16BITREG_BYTEREAD')
            else:
                ini_lines.append('MODE= 16BITREG_BYTEWRITE')

        # Add the register operation
        if op['op_type'] == 'write':
            ini_lines.append(f"REG= {op['reg_addr']},{op['reg_data']}")
        elif op['op_type'] == 'read':
            # For read operations, just add the register address
            ini_lines.append(f"REG= {op['reg_addr']}")
        # For other operation types, do nothing

    return '\n'.join(ini_lines)


def convert_vendor_to_txt(vendor_operations):
    """
    Convert vendor's raw register format to TXT format

    Args:
        vendor_operations (list): List of parsed register operations

    Returns:
        str: Content in TXT format
    """
    txt_lines = []

    # Add header
    txt_lines.append('# *************************************************************************')
    txt_lines.append('#                       FreeRTOS I2C Commands for Sensing USB Card')
    txt_lines.append('#                Converted from Vendor Format')
    txt_lines.append('# *************************************************************************')
    txt_lines.append('')

    current_slave_addr = None
    current_bus = 1

    for op in vendor_operations:
        # Handle delay operations
        if op.get('op_type') == 'delay':
            txt_lines.append(f"# DELAY= {op['delay_value']}ms")
            continue

        # Add any comments associated with this operation
        for comment in op['device']['comments']:
            txt_lines.append(comment)

        # Check if we need to switch to a new slave address
        if current_slave_addr != op['device']['addr']:
            current_slave_addr = op['device']['addr']
            # Convert 8-bit address back to 7-bit for TXT format
            addr_8bit_int = int(op['device']['addr_8bit'], 16)
            addr_7bit = hex(addr_8bit_int >> 1)
            current_slave_addr_7bit = addr_7bit

        # Add the register operation
        if op['op_type'] == 'write':
            # Format: i2cwrite bus slave_addr reg_addr width data_width data_value
            txt_lines.append(f"i2cwrite {current_bus} {current_slave_addr_7bit} {op['reg_addr']} 2 1 {op['reg_data']}")
        elif op['op_type'] == 'read':
            # Format: i2cread bus slave_addr reg_addr width num_bytes
            txt_lines.append(f"i2cread {current_bus} {current_slave_addr_7bit} {op['reg_addr']} 2 1")
        # For other operation types, do nothing

    return '\n'.join(txt_lines)


def main():
    parser = argparse.ArgumentParser(description='Unified converter for sensor capture hardware configurations')
    parser.add_argument('--mode', choices=['vendor_to_both', 'ini_to_txt', 'txt_to_ini'], required=True,
                        help='Conversion mode: vendor_to_both, ini_to_txt, or txt_to_ini')
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--output', help='Output file path (for ini_to_txt or txt_to_ini)')
    parser.add_argument('--output_ini', help='Output INI file path (for vendor_to_both)')
    parser.add_argument('--output_txt', help='Output TXT file path (for vendor_to_both)')

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

    # Perform conversion based on mode
    if args.mode == 'vendor_to_both':
        if not args.output_ini or not args.output_txt:
            print("Error: For vendor_to_both mode, both --output_ini and --output_txt are required.")
            sys.exit(1)
        
        # Parse vendor format
        vendor_operations = parse_vendor_config(input_content)
        
        # Convert to INI format
        ini_content = convert_vendor_to_ini(vendor_operations)
        
        # Convert to TXT format
        txt_content = convert_vendor_to_txt(vendor_operations)
        
        # Write output files
        try:
            with open(args.output_ini, 'w', encoding='utf-8') as f:
                f.write(ini_content)
            print(f"Successfully wrote INI file to {args.output_ini}")
        except Exception as e:
            print(f"Error writing INI file: {e}")
            sys.exit(1)
        
        try:
            with open(args.output_txt, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            print(f"Successfully wrote TXT file to {args.output_txt}")
        except Exception as e:
            print(f"Error writing TXT file: {e}")
            sys.exit(1)
    
    elif args.mode == 'ini_to_txt':
        if not args.output:
            print("Error: For ini_to_txt mode, --output is required.")
            sys.exit(1)
        
        output_content = convert_ini_to_txt(input_content)
        
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_content)
            print(f"Successfully wrote TXT file to {args.output}")
        except Exception as e:
            print(f"Error writing TXT file: {e}")
            sys.exit(1)
    
    elif args.mode == 'txt_to_ini':
        if not args.output:
            print("Error: For txt_to_ini mode, --output is required.")
            sys.exit(1)
        
        output_content = convert_txt_to_ini(input_content)
        
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_content)
            print(f"Successfully wrote INI file to {args.output}")
        except Exception as e:
            print(f"Error writing INI file: {e}")
            sys.exit(1)
    
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
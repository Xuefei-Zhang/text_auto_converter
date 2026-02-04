#!/usr/bin/env python3
"""
Vendor Configuration Converter Script for Sensor Capture Hardware

This script converts vendor's raw register configuration format to:
- INI format (for USB capture tools debugging)
- TXT format (for FreeRTOS development board debugging)

The vendor's format is a raw register format with device addresses and register values.

Usage:
    python vendor_converter.py --input vendor_config.txt --output_ini output.ini --output_txt output.txt
"""

import argparse
import re
import sys


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
        'addr_7bit': '0x00',
        'comments': []
    }
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Handle comments
        if line.startswith('#'):
            # Look for device information in comments
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
        else:
            # For read operations, just add the register address
            ini_lines.append(f"REG= {op['reg_addr']}")
    
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
        else:
            # Format: i2cread bus slave_addr reg_addr width num_bytes
            txt_lines.append(f"i2cread {current_bus} {current_slave_addr_7bit} {op['reg_addr']} 2 1")
    
    return '\n'.join(txt_lines)


def main():
    parser = argparse.ArgumentParser(description='Convert vendor raw register format to INI and TXT formats')
    parser.add_argument('--input', required=True, help='Input vendor config file path')
    parser.add_argument('--output_ini', required=True, help='Output INI file path')
    parser.add_argument('--output_txt', required=True, help='Output TXT file path')

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


if __name__ == "__main__":
    main()
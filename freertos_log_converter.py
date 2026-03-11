#!/usr/bin/env python3
"""
TI960 FreeRTOS Log to Unified TXT Converter

This script converts TI960 FreeRTOS driver log format to the unified
FreeRTOS TXT format used by unified_converter.py.

Input log format:
    [SERDES]:i2c-1 write addr: 0x3d, [0x33, 0x0]
    [Sensor]:i2c-1 write addr: 0x44, [0x3b41, 0x40]
    [SERDES]:i2c-1 read addr: 0x3d, [0x0, 0x7a]

Output TXT format:
    i2cwrite 1 0x3d 0x0033 2 1 0x00
    i2cwrite 1 0x44 0x3b41 2 1 0x40
    i2cread 1 0x3d 0x0000 2 1

Usage:
    python ti960_log_converter.py --input ti960_03c_regs.log --output freertos.txt
"""

import argparse
import re
import sys
from typing import List, Tuple, Optional


def parse_ti960_log_line(line: str) -> Optional[Tuple]:
    """
    Parse a TI960 FreeRTOS log line and extract I2C command information.

    Args:
        line: A log line like "25.831.647:[C3][I][SERDES]:i2c-1 write addr: 0x3d, [0x1, 0x1]"

    Returns:
        tuple: (command_type, bus, slave_addr, reg_addr, reg_width, data_values)
               or None if line is not an I2C command
    """
    # Pattern for I2C write commands
    # Full format: 25.831.647:[C3][I][SERDES]:i2c-1 write addr: 0x3d, [0x1, 0x1]
    # Device format: [SERDES]:i2c-1 write addr: 0x3d, [0x33, 0x0]
    # Sensor format: [Sensor]:i2c-1 write addr: 0x44, [0x3b41, 0x40]
    write_pattern = r"\[(\w+)\]:i2c-(\d+)\s+write\s+addr:\s+(0x[0-9a-fA-F]+),\s+\[(0x[0-9a-fA-F]+),\s*(0x[0-9a-fA-F]+)\]"

    write_match = re.search(write_pattern, line)
    if write_match:
        device_type = write_match.group(1)
        bus = int(write_match.group(2))
        slave_addr = write_match.group(3)
        reg_addr = write_match.group(4)
        data_value = write_match.group(5)

        # Determine register width based on register address value
        # If reg_addr > 0xFF, it's a 16-bit register address
        reg_addr_int = int(reg_addr, 16)
        reg_width = 2 if reg_addr_int > 0xFF else 1

        return "write", bus, slave_addr, reg_addr, reg_width, [int(data_value, 16)]

    # Pattern for I2C read commands
    # Full format: 25.833.308:[C3][I][SERDES]:i2c-1 read addr: 0x3d, [0x0, 0x7a]
    read_pattern = r"\[(\w+)\]:i2c-(\d+)\s+read\s+addr:\s+(0x[0-9a-fA-F]+),\s+\[(0x[0-9a-fA-F]+),\s*(0x[0-9a-fA-F]+)\]"

    read_match = re.search(read_pattern, line)
    if read_match:
        device_type = read_match.group(1)
        bus = int(read_match.group(2))
        slave_addr = read_match.group(3)
        reg_addr = read_match.group(4)
        num_bytes = read_match.group(5)

        # Determine register width based on register address value
        reg_addr_int = int(reg_addr, 16)
        reg_width = 2 if reg_addr_int > 0xFF else 1

        return "read", bus, slave_addr, reg_addr, reg_width, [int(num_bytes, 16)]

    return None


def convert_ti960_log_to_txt(log_content: str) -> str:
    """
    Convert TI960 FreeRTOS log content to unified TXT format.

    Args:
        log_content: Content from TI960 log file

    Returns:
        str: Content in unified FreeRTOS TXT format
    """
    lines = log_content.split("\n")
    txt_lines = []

    # Track current device for grouping
    current_device_type = None
    current_slave_addr = None

    # Add header
    txt_lines.append(
        "# *************************************************************************"
    )
    txt_lines.append("#                       FreeRTOS I2C Commands for TI960")
    txt_lines.append("#                Converted from TI960 FreeRTOS Log Format")
    txt_lines.append(
        "# *************************************************************************"
    )
    txt_lines.append("")

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Parse the log line
        result = parse_ti960_log_line(line)

        if result is None:
            continue

        cmd_type, bus, slave_addr, reg_addr, reg_width, data_values = result

        # Extract device type from the parsed result
        # Find the device type in the original line
        device_match = re.search(r"\[([A-Za-z]+)\]:i2c-", line)
        device_type = device_match.group(1) if device_match else "Unknown"

        # Track device changes for comments
        if device_type != current_device_type or slave_addr != current_slave_addr:
            current_device_type = device_type
            current_slave_addr = slave_addr
            txt_lines.append("")
            txt_lines.append(f"# Device: {device_type}")
            txt_lines.append(f"# I2C Slave Address: {slave_addr}")

        if cmd_type == "write":
            # Format: i2cwrite bus slave_addr reg_addr width data_width data_value
            # width is register address width (2 for 16-bit, 1 for 8-bit)
            # data_width is data value width (usually 1 for byte writes)
            data_value = data_values[0]
            reg_addr_formatted = reg_addr  # Keep original format from log
            txt_lines.append(
                f"i2cwrite {bus} {slave_addr} {reg_addr_formatted} {reg_width} 1 0x{data_value:02x}"
            )

        elif cmd_type == "read":
            # Format: i2cread bus slave_addr reg_addr width num_bytes
            num_bytes = data_values[0]
            reg_addr_formatted = reg_addr  # Keep original format from log
            txt_lines.append(
                f"i2cread {bus} {slave_addr} {reg_addr_formatted} {reg_width} 1"
            )

    return "\n".join(txt_lines)


def parse_ti960_log_file(file_path: str) -> List[Tuple]:
    """
    Parse a TI960 FreeRTOS log file and extract all I2C commands.

    Args:
        file_path: Path to the log file

    Returns:
        list: List of parsed I2C commands
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    commands = []

    for line in lines:
        result = parse_ti960_log_line(line.strip())
        if result:
            commands.append(result)

    return commands


def main():
    parser = argparse.ArgumentParser(
        description="Convert TI960 FreeRTOS log to unified TXT format"
    )
    parser.add_argument("--input", required=True, help="Input TI960 log file path")
    parser.add_argument("--output", required=True, help="Output TXT file path")
    parser.add_argument(
        "--verbose", action="store_true", help="Print detailed conversion information"
    )

    args = parser.parse_args()

    # Read input file
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            log_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    # Convert log to TXT format
    txt_content = convert_ti960_log_to_txt(log_content)

    # Write output file
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(txt_content)
        print(f"Successfully converted '{args.input}' to '{args.output}'")

        if args.verbose:
            # Count statistics
            commands = parse_ti960_log_file(args.input)
            write_count = sum(1 for cmd in commands if cmd[0] == "write")
            read_count = sum(1 for cmd in commands if cmd[0] == "read")
            print(f"  - Total I2C commands: {len(commands)}")
            print(f"  - Write commands: {write_count}")
            print(f"  - Read commands: {read_count}")

    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

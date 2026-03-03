#!/usr/bin/env python3
"""
FreeRTOS I2C Read Log Parser

Parses FreeRTOS I2C read logs and extracts successful register reads
into a simplified reg=value format.

This module can be used:
1. As a command-line script: python i2c_log_parser.py <input_log_file> [output_file]
2. As a library module: import i2c_log_parser; parse_i2c_log(content)

Usage:
    python i2c_log_parser.py <input_log_file> [output_file]

Example:
    python i2c_log_parser.py ww09_status.md
    python i2c_log_parser.py ww09_status.md parsed_regs.txt
"""

import re
from typing import List, Tuple


def parse_i2c_log(log_content: str) -> List[Tuple[str, str, str]]:
    """
    Parse FreeRTOS I2C read log and extract successful register reads.

    Args:
        log_content: The full log file content

    Returns:
        List of (slave_addr, reg_addr, value) tuples for successful reads
    """
    results = []
    lines = log_content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for i2cread command pattern: >i2cread 1 0x36 0x0100 2 1
        i2cread_match = re.match(
            r"^>i2cread\s+\d+\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+\d+\s+\d+$", line
        )

        if i2cread_match:
            slave_addr = i2cread_match.group(1)
            reg_addr = i2cread_match.group(2)

            # Look for "read success" in subsequent lines
            success_found = False
            value = None

            j = i + 1
            while j < len(lines) and j < i + 10:  # Look ahead up to 10 lines
                next_line = lines[j].strip()

                # Check for read success (with or without timestamp prefix like "295.493.329:[C3][T]read success")
                if "read success" in next_line:
                    success_found = True

                # Check for value line - can be:
                # - Pure hex: 0x0, 0xda
                # - With timestamp: 295.494.023:[C3][T]0x0
                value_match = re.search(r"(0x[0-9a-fA-F]+)$", next_line)
                if value_match and success_found:
                    value = value_match.group(1)
                    break

                # Stop if we hit "Command Complete" without finding value
                if next_line == "Command Complete":
                    break

                j += 1

            # Add to results if we found a successful read with value
            if success_found and value:
                results.append((slave_addr, reg_addr, value))

        i += 1

    return results


def format_output(results: List[Tuple[str, str, str]]) -> str:
    """
    Format parsed results into a readable output.

    Args:
        results: List of (slave_addr, reg_addr, value) tuples

    Returns:
        Formatted string with register values grouped by I2C address
    """
    output_lines = []
    current_addr = None

    for slave_addr, reg_addr, value in results:
        # Add header when I2C address changes
        if slave_addr != current_addr:
            # Add blank lines before new device section (except for first one)
            if current_addr is not None:
                output_lines.append("")
                output_lines.append("")
            output_lines.append(f"# I2C Address: {slave_addr}")
            current_addr = slave_addr

        output_lines.append(f"{reg_addr}={value}")

    return "\n".join(output_lines)


def parse_log_file(input_path, output_path=None):
    """
    Parse an I2C log file and optionally write to output.

    Args:
        input_path: Path to input log file
        output_path: Optional path to output file (if None, returns string)

    Returns:
        Tuple of (success: bool, message: str, parsed_count: int)
    """
    from pathlib import Path

    input_file = Path(input_path)

    if not input_file.exists():
        return (False, f"Input file not found: {input_file}", 0)

    # Read input log file
    with open(input_file, "r", encoding="utf-8") as f:
        log_content = f.read()

    # Parse the log
    results = parse_i2c_log(log_content)

    if not results:
        return (False, "Warning: No successful I2C reads found in the log file", 0)

    # Format output
    output = format_output(results)

    # Write to output file or return
    if output_path:
        output_file = Path(output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        return (
            True,
            f"Successfully parsed {len(results)} register reads",
            len(results),
        )
    else:
        return (True, f"Parsed {len(results)} register reads", len(results)), output

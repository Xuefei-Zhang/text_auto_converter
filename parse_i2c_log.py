#!/usr/bin/env python3
"""
FreeRTOS I2C Read Log Parser

Parses FreeRTOS I2C read logs and extracts successful register reads
into a simplified reg=value format.

Usage:
    python parse_i2c_log.py <input_log_file> [output_file]

Example:
    python parse_i2c_log.py ww09_status.md
    python parse_i2c_log.py ww09_status.md parsed_regs.txt
"""

import re
import sys
from pathlib import Path


def parse_i2c_log(log_content: str) -> list[tuple[str, str, str]]:
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


def format_output(results: list[tuple[str, str, str]]) -> str:
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


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Error: Missing input file argument")
        print("Usage: python parse_i2c_log.py <input_log_file> [output_file]")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Read input log file
    with open(input_file, "r", encoding="utf-8") as f:
        log_content = f.read()

    # Parse the log
    results = parse_i2c_log(log_content)

    if not results:
        print("Warning: No successful I2C reads found in the log file")
        sys.exit(0)

    # Format output
    output = format_output(results)

    # Write to output file or stdout
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"Successfully parsed {len(results)} register reads to: {output_file}")
    else:
        print(output)


if __name__ == "__main__":
    main()

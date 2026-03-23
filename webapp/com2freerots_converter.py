#!/usr/bin/env python3
"""
COM Realtime Log to FreeRTOS TXT Converter

This module converts COM realtime I2C write log lines like:
    [fd]18.328.100:[C3][I][LOG_DEF]:i2c-1 write addr: 0x48, [0x10, 0x11]
    [fd]18.578.532:[C3][I][Sensor]:i2c-1 write addr: 0x6c, [0x380e, 0x2b0]

into FreeRTOS TXT commands like:
    i2cwrite 1 0x48 0x10 1 1 0x11
    i2cwrite 1 0x6c 0x380e 2 2 0x2b0
"""

import re
from typing import Dict, Optional


COM_WRITE_PATTERN = re.compile(
    r"\[fd\]\d+\.\d+\.\d+:\[C\d+\]\[I\]\[([^\]]+)\]:"
    r"i2c-(\d+)\s+write\s+addr:\s+(0x[0-9a-fA-F]+),\s+"
    r"\[(0x[0-9a-fA-F]+),\s*(0x[0-9a-fA-F]+)\]"
)


def _hex_width(hex_value: str) -> int:
    digits = hex_value[2:]
    return max(1, (len(digits) + 1) // 2)


def _normalize_hex(hex_value: str) -> str:
    return f"0x{hex_value[2:].lower()}"


def _format_data_value(hex_value: str, data_width: int) -> str:
    digits = hex_value[2:].lower()
    if data_width == 1:
        return f"0x{digits.zfill(2)}"
    return f"0x{digits}"


def parse_com_log_line(line: str) -> Optional[Dict[str, object]]:
    match = COM_WRITE_PATTERN.search(line.strip())
    if not match:
        return None

    tag, bus, slave_addr, register_addr, data_value = match.groups()

    return {
        "tag": tag,
        "bus": int(bus),
        "slave_addr": _normalize_hex(slave_addr),
        "register_addr": _normalize_hex(register_addr),
        "register_width": _hex_width(register_addr),
        "data_width": _hex_width(data_value),
        "data_value": _normalize_hex(data_value),
    }


def convert_com_log_to_txt(log_content: str) -> str:
    txt_lines = [
        "# *************************************************************************",
        "#                    FreeRTOS I2C Commands for COM Logs",
        "#                Converted from COM Realtime I2C Write Logs",
        "# *************************************************************************",
        "",
    ]

    current_tag = None
    current_slave_addr = None

    for raw_line in log_content.splitlines():
        parsed = parse_com_log_line(raw_line)
        if parsed is None:
            continue

        tag = parsed["tag"]
        slave_addr = parsed["slave_addr"]
        if tag != current_tag or slave_addr != current_slave_addr:
            current_tag = tag
            current_slave_addr = slave_addr
            txt_lines.append("")
            txt_lines.append(f"# Device: {tag}")
            txt_lines.append(f"# I2C Slave Address: {slave_addr}")

        txt_lines.append(
            "i2cwrite "
            f"{parsed['bus']} {parsed['slave_addr']} {parsed['register_addr']} "
            f"{parsed['register_width']} {parsed['data_width']} "
            f"{_format_data_value(parsed['data_value'], parsed['data_width'])}"
        )

    return "\n".join(txt_lines)

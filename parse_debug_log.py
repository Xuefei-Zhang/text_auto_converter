import re

def parse_debug_log(log_text):
    """
    Parse the debug log to extract device address, register address, and values.
    
    Args:
        log_text (str): The raw debug log text
        
    Returns:
        list: List of tuples containing (device_addr, reg_addr, values)
    """
    # Regular expression to match the i2cread command and its results
    # Pattern looks for: i2cread 1 [device_addr] [reg_addr] 2 [num_bytes]
    # followed by the actual values read
    pattern = r'i2cread 1 (0x[0-9a-fA-F]+) (0x[0-9a-fA-F]+) 2 \d+\s*\n(.*?)\nCommand Complete'
    
    results = []
    
    matches = re.findall(pattern, log_text, re.DOTALL)
    
    for match in matches:
        device_addr = match[0]
        reg_addr = match[1]
        
        # Extract the values from the read success section
        value_section = match[2]
        # Look for lines that contain hex values like "0xXX"
        value_lines = re.findall(r'0x[0-9a-fA-F]+', value_section)
        values = [val.lower() for val in value_lines]  # Normalize to lowercase
        
        results.append((device_addr, reg_addr, values))
    
    return results

def format_output(results):
    """
    Format the parsed results into a clean table-like structure.
    
    Args:
        results (list): List of tuples containing (device_addr, reg_addr, values)
        
    Returns:
        str: Formatted output string
    """
    output = "Device Address | Register Address | Values\n"
    output += "-" * 50 + "\n"
    
    for device_addr, reg_addr, values in results:
        values_str = " ".join(values)
        output += f"{device_addr:>12} | {reg_addr:>14} | {values_str}\n"
    
    return output

def main():
    import sys

    # Check if a filename was provided as an argument
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as file:
                log_text = file.read()
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            return
    else:
        # Use sample log text if no file provided
        log_text = """# *************************************************************************

Command not recognised.  Enter 'help' to view a list of available commands.


>#                       Debug Checkpoint Registers

Command not recognised.  Enter 'help' to view a list of available commands.


># *************************************************************************

Command not recognised.  Enter 'help' to view a list of available commands.


>


># --- OX08D10 (Sensor) Status Checks ---

Command not recognised.  Enter 'help' to view a list of available commands.


># Check Streaming Status (0x0100): Should be 0x01 to confirm streaming enabled

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x36 0x0100 2 1

64197.544.808:[C3][T]read success
64197.545.545:[C3][T]0x1

Command Complete

># Check Frame Counter (0x483E/0x483F): Values should increment to show sensor data output

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x36 0x483e 2 2

64197.551.394:[C3][T]read success
64197.552.131:[C3][T]0x0
64197.552.710:[C3][T]0x0

Command Complete

># Check Internal Fault Flags (0x4F08/0x4F09): BLC or timing errors (0x4F09 should be 0x00)

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x36 0x4f08 2 2

64197.558.580:[C3][T]read success
64197.559.316:[C3][T]0x67
64197.559.917:[C3][T]0xfe

Command Complete

># Check MIPI Lane Configuration (0x3012): Should be 0x41 for 4-lane mode

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x36 0x3012 2 1

64197.565.392:[C3][T]read success
64197.566.129:[C3][T]0x21

Command Complete


># --- MAX96717 (Serializer) Status Checks ---

Command not recognised.  Enter 'help' to view a list of available commands.


># Check GMSL Link Lock (0x0013): Physical connection (Bit 3 should be 1)

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x42 0x0013 2 1

64197.574.692:[C3][T]read success
64197.575.428:[C3][T]0xda

Command Complete

># Check Pixel Clock Detection (0x0112): PCLKDET (Bit 7) should be 1 to confirm sensor clock received

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x42 0x0112 2 1

64197.581.502:[C3][T]read success
64197.582.239:[C3][T]0xa

Command Complete

># Check MIPI Input Lane Count (0x331): Should match sensor's 4-lane setting (0x30)

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x42 0x0331 2 1

64197.587.903:[C3][T]read success
64197.588.640:[C3][T]0x30

Command Complete

># Check MIPI Input Errors (0x0343/0x0344): Should be 0x00 for no ECC/CRC errors

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x42 0x0343 2 2

64197.594.295:[C3][T]read success
64197.595.031:[C3][T]0x0
64197.595.611:[C3][T]0x0

Command Complete

># Check MIPI Input Clock Count (0x0390): Value should change dynamically indicating hardware connection

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x42 0x0390 2 1

64197.601.726:[C3][T]read success
64197.602.463:[C3][T]0x74

Command Complete


># --- MAX9296 (Deserializer) Status Checks ---

Command not recognised.  Enter 'help' to view a list of available commands.


># Check GMSL Link Lock (0x0013): Physical link status with serializer

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x0013 2 1

64197.610.983:[C3][T]read success
64197.611.720:[C3][T]0xda

Command Complete

># Check Video Pipeline Z Packet Detection (0x012C): VID_PKT_DET (Bit 5) and VID_LOCK (Bit 6) should be 1

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x012c 2 1

64197.617.879:[C3][T]read success
64197.618.615:[C3][T]0x2

Command Complete

># Check CSI Routing Map (0x04AD): Pipe Z should map to DPHY2/Port B (should be 0x80)

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x04ad 2 1

64197.624.324:[C3][T]read success
64197.625.061:[C3][T]0x80

Command Complete

># Check CSI PLL Lock Status (0x0308): Output clock lock (with Port B, Bit 6 should be 1)

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x0308 2 1

64197.630.875:[C3][T]read success
64197.631.612:[C3][T]0x1

Command Complete

># Check CSI Output Total Enable (0x0313): Output switch should be open (should be 0x02)

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x0313 2 1

64197.637.385:[C3][T]read success
64197.638.121:[C3][T]0x2

Command Complete

># Check Port B Output Frequency (0x0323): Rate setting should match SoC requirements

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x0323 2 1

64197.643.829:[C3][T]read success
64197.644.566:[C3][T]0x2f

Command Complete

># Check Pipeline Heartbeat Setting (0x012A): Heartbeat match (recommend value 0x0A)

Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x012a 2 1
64198.580.134:[C3][T]read success
64198.580.870:[C3][T]0x2

Command Complete"""

    results = parse_debug_log(log_text)
    formatted_output = format_output(results)

    # Create the full output
    full_output = formatted_output
    full_output += "\n\nSummary by Device:\n"
    full_output += "-" * 30 + "\n"

    devices = {}
    for device_addr, reg_addr, values in results:
        if device_addr not in devices:
            devices[device_addr] = []
        devices[device_addr].append((reg_addr, values))

    for device_addr, registers in devices.items():
        full_output += f"\nDevice {device_addr}:\n"
        for reg_addr, values in registers:
            values_str = " ".join(values)
            full_output += f"  {reg_addr}: {values_str}\n"

    # Print to console
    print(full_output)

    # Write to file
    output_filename = "correct_test_results.txt"
    with open(output_filename, 'w') as output_file:
        output_file.write(full_output)

    print(f"\nResults saved to {output_filename}")

if __name__ == "__main__":
    main()
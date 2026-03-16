># --- MAX9625 (Serializer) Status Checks ---
Command not recognised.  Enter 'help' to view a list of available commands.


># Check GMSL Link Lock (0x0013): Physical connection (Bit 3 should be 1)
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x40 0x0013 2 1
1588.940.900:[C1][T]read success
1588.941.616:[C1][T]0xda

Command Complete

># Check Pixel Clock Detection (0x0112): PCLKDET (Bit 7) should be 1 to confirm sensor clock received
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x40 0x0112 2 1
1589.180.719:[C1][T]read success
1589.181.434:[C1][T]0x8a

Command Complete

># Check MIPI Input Lane Count (0x331): Should match sensor's 4-lane setting (0x30)
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x40 0x0331 2 1
1589.439.285:[C1][T]read success
1589.440.001:[C1][T]0x30

Command Complete

># Check MIPI Input Errors (0x0343/0x0344): Should be 0x00 for no ECC/CRC errors
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x40 0x0343 2 2
1589.682.398:[C1][T]read success
1589.683.113:[C1][T]0x0
1589.683.671:[C1][T]0x0

Command Complete

># Check MIPI Input Clock Count (0x0390): Value should change dynamically indicating hardware connection
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x40 0x0390 2 1
1589.940.017:[C1][T]read success
1589.940.732:[C1][T]0x19

Command Complete

>

># --- MAX9296 (Deserializer) Status Checks ---
Command not recognised.  Enter 'help' to view a list of available commands.


># Check GMSL Link Lock (0x0013): Physical link status with serializer
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x0013 2 1
1590.432.596:[C1][T]read success
1590.433.311:[C1][T]0xea

Command Complete

># Check Video Pipeline Z Packet Detection (0x012C): VID_PKT_DET (Bit 5) and VID_LOCK (Bit 6) should be 1
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x012c 2 1
1590.684.816:[C1][T]read success
1590.685.531:[C1][T]0x2

Command Complete

># Check CSI Routing Map (0x04AD): Pipe Z should map to DPHY2/Port B (should be 0x80)
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x04ad 2 1
1590.942.355:[C1][T]read success
1590.943.070:[C1][T]0x0

Command Complete

># Check CSI PLL Lock Status (0x0308): Output clock lock (with Port B, Bit 6 should be 1)
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x0308 2 1
1591.195.626:[C1][T]read success
1591.196.342:[C1][T]0x61

Command Complete

># Check CSI Output Total Enable (0x0313): Output switch should be open (should be 0x02)
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x0313 2 1
1591.437.419:[C1][T]read success
1591.438.134:[C1][T]0x2

Command Complete

># Check Port B Output Frequency (0x0323): Rate setting should match SoC requirements
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x0323 2 1
1591.696.125:[C1][T]read success
1591.696.840:[C1][T]0x26

Command Complete

># Check Pipeline Heartbeat Setting (0x012A): Heartbeat match (recommend value 0x0A)
Command not recognised.  Enter 'help' to view a list of available commands.


>i2cread 1 0x48 0x012a 2 1
1593.926.251:[C1][T]read success
1593.926.966:[C1][T]0x2

Command Complete

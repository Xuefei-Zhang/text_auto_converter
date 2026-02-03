根据历史对话中对 **OX08D10 (Sensor)**、**MAX96717 (Serializer)** 和 **MAX9296 (Deserializer)** 的故障排查逻辑，以下为您梳理的完整状态检查寄存器组。

**说明：**

- **Bus ID:** 1
- **Slave Addr:** 已根据要求将历史记录中的 8-bit 地址转换为 **7-bit 格式**（Sensor 0x36, Serializer 0x42, Deserializer 0x48）。
- **Bus Width:** 以上设备寄存器地址均为 **2 字节 (16-bit)**。
- **格式:** `i2cread <bus_id> <slave> <reg_addr> <bus_width> <read_len>`

---

### 1. Camera Sensor (OX08D10) 状态检查

用于确认 Sensor 是否正常 Streaming 以及是否存在内部逻辑故障。

- **检查 Streaming 状态 (0x0100):** 确认是否已开启流输出（应为 0x01）。
  `i2cread 1 0x36 0x0100 2 1`
- **检查帧计数器 (0x483E/0x483F):** 连续读取两次，数值增加说明 Sensor 正在输出数据包。
  `i2cread 1 0x36 0x483e 2 2`
- **检查内部故障标志 (0x4F08/0x4F09):** 确认 BLC（黑电平校准）或时序是否有错（0x4F09 正常应为 0x00）。
  `i2cread 1 0x36 0x4f08 2 2`
- **检查 MIPI Lane 配置 (0x3012):** 确认是否处于 4-lane 模式（应为 0x41）。
  `i2cread 1 0x36 0x3012 2 1`

---

### 2. Serializer (MAX96717) 状态检查

用于确认串行器是否正确接收到 Sensor 的 MIPI 信号并转换至 GMSL 链路。

- **检查 GMSL 链路锁定 (0x0013):** 确认物理连接（Bit 3 应为 1）。
  `i2cread 1 0x42 0x0013 2 1`
- **检查像素时钟检测 (0x0112):** PCLKDET (Bit 7) 应为 1，确认收到 Sensor 时钟。
  `i2cread 1 0x42 0x0112 2 1`
- **检查 MIPI 输入 Lane 数量 (0x331):** 确认是否匹配 Sensor 的 4-lane 设置（应为 0x30）。
  `i2cread 1 0x42 0x0331 2 1`
- **检查 MIPI 输入错误 (0x0343/0x0344):** 确认是否存在 ECC/CRC 错误（应全为 0x00）。
  `i2cread 1 0x42 0x0343 2 2`
- **检查 MIPI 输入时钟计数 (0x0390):** 数值动态变化说明硬件连接正常。
  `i2cread 1 0x42 0x0390 2 1`

---

### 3. Deserializer (MAX9296) 状态检查

用于确认解串器是否识别到视频流，并正确路由至输出端口（假设使用 Port B）。

- **检查 GMSL 链路锁定 (0x0013):** 确认与串行器的物理链路状态。
  `i2cread 1 0x48 0x0013 2 1`
- **检查视频管道 Z 数据包识别 (0x012C):** VID_PKT_DET (Bit 5) 应为 1，VID_LOCK (Bit 6) 应为 1。
  `i2cread 1 0x48 0x012c 2 1`
- **检查 CSI 路由映射 (0x04AD):** 确认 Pipe Z 是否映射到 DPHY2/Port B（应为 0x80）。
  `i2cread 1 0x48 0x04ad 2 1`
- **检查 CSI PLL 锁定状态 (0x0308):** 确认输出时钟是否锁定（使用 Port B 时，Bit 6 应为 1）。
  `i2cread 1 0x48 0x0308 2 1`
- **检查 CSI 输出总使能 (0x0313):** 确认输出开关是否已打开（应为 0x02）。
  `i2cread 1 0x48 0x0313 2 1`
- **检查 Port B 输出频率 (0x0323):** 确认速率设置是否符合 SoC 要求。
  `i2cread 1 0x48 0x0323 2 1`
- **检查管道心跳设置 (0x012A):** 确认心跳匹配（建议值为 0x0A）。
  `i2cread 1 0x48 0x012a 2 1`

---

### 故障判断断点建议

1. **如果 `0x36, 0x483E` 不变：** 问题在 Sensor 端的初始化序列或电源。
2. **如果 `0x42, 0x0343` 报错：** 问题在 Sensor 到 Serializer 的 MIPI Lane 映射或 `t_hs_settle` 时序不匹配。
3. **如果 `0x48, 0x012C` 只有检测 (0x22) 但未锁定 (0x62)：** 检查心跳 `0x12A` 和 Sensor 输出时序的稳定性。
4. **如果 `0x48, 0x0308` 未锁定：** 检查 `0x4AD` 路由指向和 `0x323` 输出频率配置是否正确。

# ---------------- test result ----------

## "Sensing_max9296_max9295_ovOX03C_27mclk_MIPI_1920x1280_raw12_30fps.ini" test 03c on USB Capturesensing ✅
### 默认settings 解析：
```
1. 串行器 (MAX9295A - 0x40)
寄存器 0x0057 = 0x12
寄存器名称：TX3 (属于 Video Pipeline Y 块)
位域解析：
Bit 4 (TX_SPLT_MASK_A) = 1：在分割模式（Splitter Mode）下，强制将此管道的数据包通过 GMSL Link A 发送。
Bit 1:0 (TX_STR_SEL) = 0b10 (即 2)：设置发送数据包的 Stream ID 为 2。
功能说明：该配置定义了视频管道 Y 的传输属性，将其识别码设为 Stream 2，并确保它从物理端口 A 输出。
寄存器 0x005B = 0x11
寄存器名称：TX3 (属于 Video Pipeline Z 块)
位域解析：
Bit 4 (TX_SPLT_MASK_A) = 1：同样确保数据在分割模式下通过 Link A 发送。
Bit 1:0 (TX_STR_SEL) = 0b01 (即 1)：设置发送数据包的 Stream ID 为 1。
功能说明：将视频管道 Z 识别为 Stream 1。这通常用于多摄像头同步或 HDR 多流传输，通过不同的 Stream ID 区分不同的视频分量。
寄存器 0x0318 = 0x6C
寄存器名称：FRONTTOP_16
位域解析：
Bit 6:0 (mem_dt1_selz) = 0x2C（0x6C 去除最高位或结合 MSB 使能标志）：选择路由到视频管道 Z 的指定数据类型（Data Type）。
功能说明：这是一个前端路由寄存器。在 MIPI CSI-2 协议中，0x2C 对应 RAW12 数据格式。此设置告诉串行器：“将接收到的所有 RAW12 格式的数据包引导至视频管道 Z 进行处理”。

--------------------------------------------------------------------------------
2. 解串器 (MAX9296A - 0x48)
寄存器 0x0320 = 0x26
寄存器名称：BACKTOP25 (控制 CSI 控制器 1 / Port A)
位域解析：
Bit 5 (phy1_csi_tx_dpll_fb_fraction_predef_en) = 1：使能 MIPI 发送端 DPLL 的预设频率模式。
Bit 4:0 (phy1_csi_tx_dpll_predef_freq) = 0x06：设定预设频率。根据查找表，0x06 代表 600Mbps。
功能说明：配置解串器向 SoC 发送数据时的 MIPI 接口速率。您的硬件目前被配置为以每通道 600Mbps 的速度输出视频。
寄存器 0x0313 = 0x02
寄存器名称：BACKTOP12
位域解析：
Bit 1 (CSI_OUT_EN) = 1：显式使能 MIPI CSI-2 输出端口。
功能说明：这是整个输出链路的“总开关”。如果此位为 0，MIPI 引脚将保持在 LP11（低功耗）状态；设置为 1 后，只要内部视频管道获得锁定，解串器就会开始驱动物理引脚进行高速数据传输。
总结配置逻辑
这一套配置的整体意图是：串行器接收来自传感器的 RAW12 数据并标记为 Stream 1/2，通过 GMSL Link A 发送；解串器接收后，通过 Port A 以 600Mbps 的速率将视频流转发给 SoC。
```



##  "Sensing_max9296_max9295_ovOX03C_27mclk_MIPI_1920x1280_raw12_30fps_freertos_converted_20260305_155125"  converted 03c on hkr ❌

### 下一步调试hkr 上面，
- 1. change pixter test mipi datarate from 1500 to 600.  still failed ❌
 
```
343.590.155:[C3][I][IPU]:DPHY0 aggregation mode 200ohm termination
343.591.817:[C3][I][IPU]:DPHY0 power up successfully, state 0x7
343.593.203:[C3][I][IPU]:set DPHY1 bit rate 600Mbps
343.594.565:[C3][I][IPU]:DPHY1 power up successfully, state 0x7
343.595.954:[C3][I][Sensor]:sensor mode(1920x1280) format(91) 0/0 fps selected
343.597.688:[C3][I][IPU]:streamon at 8246344500
343.598.868:[C3][P][IPU]:hostlib: libcall stream 0 capture hw_fid 1 systimer 8246372820
348.599.218:[C3][E][IPU]:isys stream 0 dqevent timeout(-1) errno 60
353.613.217:[C3][E][IPU]:isys stream 0 dqevent timeout(-1) errno 60
358.627.220:[C3][E][IPU]:isys stream 0 dqevent timeout(-1) errno 60
```


- 2. change serdes settings, pass gmsl data in deserailizer to csi port B, still failed ❌
- change settings to : 
```
#new
i2cwrite 1 0x48 0x0308 2 1 0x0F
i2cwrite 1 0x48 0x0323 2 1 0x26

i2cwrite 1 0x48 0x0313 2 1 0x02
```
- above test analyze by read some regs:
```
配置误区提示：在解串器（MAX9296A）中，寄存器 0x0308 主要用于显示 PLL 锁定状态，并不像串行器那样控制管道路由。要让数据从 Port B 输出，您可能需要配置 MIPI_TX 2 控制器块（0x48B 起始的寄存器）来显式映射管道 Y 的 Stream ID。
```

```
直通模式 (Pass-through)：手册中有一句非常关键的描述——“Non-matched virtual channel (VC) and data types (DT) pass to the corresponding CSI2 controller.”（未被匹配的数据将流向其对应的 CSI-2 控制器）。
默认对应关系：在解串器的物理设计中，Video Pipe X 和 Pipe Y 默认对应的就是 Aggregator A (Port A)。因此，即便您不写任何映射条目，Pipe Y 的数据也会因为这种“默认对应关系”而流向 Port A

2. 为什么 Port B 配置了映射，数据就不会被 Port A “选走”？
这是一个优先级和排他性的问题：
逻辑匹配优先级 > 默认对应关系： 当 Pipe Y 的行缓存填满时，系统会先检查所有控制器的显式映射表。由于您在 MIPI_TX 2 (Port B) 中使能了条目 0 并匹配了 VCID/DT，聚合器 B 此时拥有逻辑上的认领权。
数据的排他性读取： 手册明确指出：每个行缓存虽然连接到两个聚合器，但同一行数据只能被读出一次。一旦数据被其中一个聚合器（在这个测试中是编程过的 Aggregator B）领走，它就会从缓存中“消失”，另一个聚合器（Aggregator A）将无法再次读取。
确定性指定： 通过在控制器 2 中设置 MAP_SRC_0 (0x48D) 和 MAP_DPHY_DEST_0 (0x4AD)，您实际上是将原本“无主”或“默认归 A”的数据，显式重定向到了物理 Port B。
```
still failed ❌

# ---------------- Next step: -----------------------------
- check with yaohao about hkr + max929695 03c ❓
- test port b on 森云, still work ✅ (森云port A/B 都支持？？, 猜是的，因为软件里面还能同时打开两个camera）
- read 0x482/0x442 在森云上面，判断这个寄存器确实适用于检查 csi port 发送图像了 ❌, 不能用这个寄存器判断，当前在出图，但是寄存器依然是0
```
[18:37:14] <read OK> 90, 0442, 00
[18:37:15] <read OK> 90, 0442, 00
[18:37:20] <read OK> 90, 0482, 00
[18:37:20] <read OK> 90, 0482, 00
```



# ---------------- Next step: -----------------------------
- check about hkr + max929695 03c port B, 用dmtest , still failed ❌
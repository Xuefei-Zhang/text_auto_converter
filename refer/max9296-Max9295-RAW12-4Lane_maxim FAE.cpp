/*
# Name: Petri.Zhu
# Date: 2024/5/27
# Version: 6.5.6
#
# I2C Address(0x), Register Address(0x), Register Value(0x), Read Modify Write(0x)
#
# THIS DATA FILE, AND ALL INFORMATION CONTAINED THEREIN,
# IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL ANALOG DEVICES, INC. BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE DATA FILE,
# THE INFORMATION CONTAINED THEREIN, OR ITS USE FOR ANY PURPOSE.
# BEFORE USING THIS DATA FILE IN ANY APPLICATION FOR PRODUCTION OR DEPLOYMENT,
# THE CUSTOMER IS SOLELY RESPONSIBLE FOR TESTING AND VERIFYING
# THE CONTENT OF THIS DATA FILE IN CONNECTION WITH THEIR PRODUCTS AND SYSTEM(S).
# ---------------------------------------------------------------------------------
#
#            _____ _____  
#      /\   |  __ \_   _| 
#     /  \  | |  | || |   
#    / /\ \ | |  | || |   
#   / ____ \| |__| || |_  
#  /_/    \_\_____/_____| 
#
# ---------------------------------------------------------------------------------
*/
/*
# This script is validated on: 
# MAX9295A
# MAX9296A
# Please refer to the Errata sheet for each device.
# ---------------------------------------------------------------------------------
*/
// GMSL-A / Serializer: MAX9295A (Pixel Mode) / Mode: 1x4 / Device Address: 0x80 / Multiple-VC Case: Single VC / Multiple-VC Pipe Sharing: N/A
// PipeX:
// Input Stream: VC0 RAW12 PortB (D-PHY)

// GMSL-B / Serializer: MAX9295A (Pixel Mode) / Mode: 1x4 / Device Address: 0x80 / Multiple-VC Case: Single VC / Multiple-VC Pipe Sharing: N/A
// PipeX:
// Input Stream: VC0 RAW12 PortB (D-PHY)

// Deserializer: MAX9296A / Mode: 2 (1x4) / Device Address: 0x90
// PipeX:
// GMSL-A Input Stream: VC0 RAW12 PortB - Output Stream: VC0 RAW12 PortA (D-PHY)
// PipeY:
// GMSL-B Input Stream: VC0 RAW12 PortB - Output Stream: VC1 RAW12 PortA (D-PHY)

0x04,0x90,0x03,0x13,0x00, //  (CSI_OUT_EN): CSI output disabled
// Single Link Initialization Before Serializer Device Address Change
0x04,0x90,0x00,0x10,0x22, //  (AUTO_LINK): Disabled |  (LINK_CFG): 0x2 |  (RESET_ONESHOT): Activated
0x00,0x78, // 120 msec delay
// GMSL-B Serializer Address Change from 0x80 to 0x82
0x04,0x80,0x00,0x00,0x82, //  (DEV_ADDR): 0x41
0x04,0x82,0x00,0x7B,0x12, //  (TX_SRC_ID): 0x2
0x04,0x82,0x00,0x83,0x12, //  (TX_SRC_ID): 0x2
0x04,0x82,0x00,0x8B,0x12, //  (TX_SRC_ID): 0x2
0x04,0x82,0x00,0x93,0x12, //  (TX_SRC_ID): 0x2
0x04,0x82,0x00,0xA3,0x12, //  (TX_SRC_ID): 0x2
0x04,0x82,0x00,0xAB,0x12, //  (TX_SRC_ID): 0x2
// Link Initialization for Deserializer
0x04,0x90,0x00,0x10,0x23, // (Default)  (AUTO_LINK): Disabled |  (LINK_CFG): 0x3 | (Default)  (RESET_ONESHOT): Activated
0x00,0x78, // 120 msec delay
// Video Transmit Configuration for Serializer(s)
0x04,0x80,0x00,0x02,0x43, //  (VID_TX_EN_X): Disabled
0x04,0x82,0x00,0x02,0x43, //  (VID_TX_EN_X): Disabled
//  
// INSTRUCTIONS FOR GMSL-A SERIALIZER MAX9295A
//  
// MIPI DPHY Configuration
0x04,0x80,0x03,0x30,0x00, // (Default)  (Port Configuration): 1x4
0x04,0x80,0x03,0x31,0x33, // (Default)  (Port B - Lane Count): 4
0x04,0x80,0x03,0x32,0xE0, // (Default)  (Lane Map - PHY1 D0): Lane 2 | (Default)  (Lane Map - PHY1 D1): Lane 3
0x04,0x80,0x03,0x33,0x04, // (Default)  (Lane Map - PHY2 D0): Lane 0 | (Default)  (Lane Map - PHY2 D1): Lane 1
0x04,0x80,0x03,0x34,0x00, // (Default)  (Polarity - PHY1 Lane 0): Normal | (Default)  (Polarity - PHY1 Lane 1): Normal
0x04,0x80,0x03,0x35,0x00, // (Default)  (Polarity - PHY2 Lane 0): Normal | (Default)  (Polarity - PHY2 Lane 1): Normal | (Default)  (Polarity - PHY2 Clock Lane): Normal
// Controller to Pipe Mapping Configuration
0x04,0x80,0x03,0x08,0x7D, //  (CLK_SELX): Port B | (Default)  (START_PORTB): Enabled
0x04,0x80,0x03,0x11,0x15, // (Default)  (START_PORTBX): Start Video | (Default)  (START_PORTBY): Not Started |  (START_PORTBZ): Not Started | (Default)  (START_PORTBU): Not Started
0x04,0x80,0x03,0x14,0x6C, //  (mem_dt1_selx): 0x6C
0x04,0x80,0x03,0x15,0x00, // (Default)  (independent_vs_mode): Disabled
// Double Mode Configuration
0x04,0x80,0x03,0x13,0x10, //  (bpp12dblx): Send 12-bit pixels as 24-bit
0x04,0x80,0x03,0x1C,0x38, // (Default)  (soft_bppx): 0x18 |  (soft_bppx_en): Software override enabled
// Pipe Configuration
0x04,0x80,0x00,0x53,0x10, // (Default)  (TX_STR_SEL Pipe X): 0x0
//  
// INSTRUCTIONS FOR GMSL-B SERIALIZER MAX9295A
//  
// MIPI DPHY Configuration
0x04,0x82,0x03,0x30,0x00, // (Default)  (Port Configuration): 1x4
0x04,0x82,0x03,0x31,0x33, // (Default)  (Port B - Lane Count): 4
0x04,0x82,0x03,0x32,0xE0, // (Default)  (Lane Map - PHY1 D0): Lane 2 | (Default)  (Lane Map - PHY1 D1): Lane 3
0x04,0x82,0x03,0x33,0x04, // (Default)  (Lane Map - PHY2 D0): Lane 0 | (Default)  (Lane Map - PHY2 D1): Lane 1
0x04,0x82,0x03,0x34,0x00, // (Default)  (Polarity - PHY1 Lane 0): Normal | (Default)  (Polarity - PHY1 Lane 1): Normal
0x04,0x82,0x03,0x35,0x00, // (Default)  (Polarity - PHY2 Lane 0): Normal | (Default)  (Polarity - PHY2 Lane 1): Normal | (Default)  (Polarity - PHY2 Clock Lane): Normal
// Controller to Pipe Mapping Configuration
0x04,0x82,0x03,0x08,0x7D, //  (CLK_SELX): Port B | (Default)  (START_PORTB): Enabled
0x04,0x82,0x03,0x11,0x15, // (Default)  (START_PORTBX): Start Video | (Default)  (START_PORTBY): Not Started |  (START_PORTBZ): Not Started | (Default)  (START_PORTBU): Not Started
0x04,0x82,0x03,0x14,0x6C, //  (mem_dt1_selx): 0x6C
0x04,0x82,0x03,0x15,0x00, // (Default)  (independent_vs_mode): Disabled
// Double Mode Configuration
0x04,0x82,0x03,0x13,0x10, //  (bpp12dblx): Send 12-bit pixels as 24-bit
0x04,0x82,0x03,0x1C,0x38, // (Default)  (soft_bppx): 0x18 |  (soft_bppx_en): Software override enabled
// Pipe Configuration
0x04,0x82,0x00,0x53,0x10, // (Default)  (TX_STR_SEL Pipe X): 0x0
//  
// INSTRUCTIONS FOR DESERIALIZER MAX9296A
//  
// Video Pipes And Routing Configuration
0x04,0x90,0x00,0x50,0x00, // (Default)  (STR_SELX): 0x0
0x04,0x90,0x00,0x51,0x00, //  (STR_SELY): 0x0
// Pipe to Controller Mapping Configuration
0x04,0x90,0x04,0x0B,0x07, //  (MAP_EN_L Pipe X): 0x7
0x04,0x90,0x04,0x0C,0x00, // (Default)  (MAP_EN_H Pipe X): 0x0
0x04,0x90,0x04,0x0D,0x2C, //  (MAP_SRC_0 Pipe X DT): 0x2C | (Default)  (MAP_SRC_0 Pipe X VC): 0x0
0x04,0x90,0x04,0x0E,0x2C, //  (MAP_DST_0 Pipe X DT): 0x2C | (Default)  (MAP_DST_0 Pipe X VC): 0x0
0x04,0x90,0x04,0x0F,0x00, // (Default)  (MAP_SRC_1 Pipe X DT): 0x0 | (Default)  (MAP_SRC_1 Pipe X VC): 0x0
0x04,0x90,0x04,0x10,0x00, // (Default)  (MAP_DST_1 Pipe X DT): 0x0 | (Default)  (MAP_DST_1 Pipe X VC): 0x0
0x04,0x90,0x04,0x11,0x01, //  (MAP_SRC_2 Pipe X DT): 0x1 | (Default)  (MAP_SRC_2 Pipe X VC): 0x0
0x04,0x90,0x04,0x12,0x01, //  (MAP_DST_2 Pipe X DT): 0x1 | (Default)  (MAP_DST_2 Pipe X VC): 0x0
0x04,0x90,0x04,0x2D,0x15, //  (MAP_DPHY_DST_0 Pipe X): 0x1 |  (MAP_DPHY_DST_1 Pipe X): 0x1 |  (MAP_DPHY_DST_2 Pipe X): 0x1
0x04,0x90,0x04,0x4B,0x07, //  (MAP_EN_L Pipe Y): 0x7
0x04,0x90,0x04,0x4C,0x00, // (Default)  (MAP_EN_H Pipe Y): 0x0
0x04,0x90,0x04,0x4D,0x2C, //  (MAP_SRC_0 Pipe Y DT): 0x2C | (Default)  (MAP_SRC_0 Pipe Y VC): 0x0
0x04,0x90,0x04,0x4E,0x6C, //  (MAP_DST_0 Pipe Y DT): 0x2C |  (MAP_DST_0 Pipe Y VC): 0x1
0x04,0x90,0x04,0x4F,0x00, // (Default)  (MAP_SRC_1 Pipe Y DT): 0x0 | (Default)  (MAP_SRC_1 Pipe Y VC): 0x0
0x04,0x90,0x04,0x50,0x40, // (Default)  (MAP_DST_1 Pipe Y DT): 0x0 |  (MAP_DST_1 Pipe Y VC): 0x1
0x04,0x90,0x04,0x51,0x01, //  (MAP_SRC_2 Pipe Y DT): 0x1 | (Default)  (MAP_SRC_2 Pipe Y VC): 0x0
0x04,0x90,0x04,0x52,0x41, //  (MAP_DST_2 Pipe Y DT): 0x1 |  (MAP_DST_2 Pipe Y VC): 0x1
0x04,0x90,0x04,0x6D,0x15, //  (MAP_DPHY_DST_0 Pipe Y): 0x1 |  (MAP_DPHY_DST_1 Pipe Y): 0x1 |  (MAP_DPHY_DST_2 Pipe Y): 0x1
// Double Mode Configuration
0x04,0x90,0x04,0x73,0x01, //  (ALT_MEM_MAP12 CTRL1): Alternate memory map enabled
// MIPI DPHY Configuration
0x04,0x90,0x03,0x30,0x04, // (Default)  (Port Configuration): 2 (1x4)
0x04,0x90,0x04,0x4A,0xD0, // (Default)  (Port A - Lane Count): 4
0x04,0x90,0x03,0x33,0x4E, // (Default)  (Lane Map - PHY0 D0): Lane 2 | (Default)  (Lane Map - PHY0 D1): Lane 3 | (Default)  (Lane Map - PHY1 D0): Lane 0 | (Default)  (Lane Map - PHY1 D1): Lane 1
0x04,0x90,0x03,0x35,0x00, // (Default)  (Polarity - PHY0 Lane 0): Normal | (Default)  (Polarity - PHY0 Lane 1): Normal | (Default)  (Polarity - PHY1 Lane 0): Normal | (Default)  (Polarity - PHY1 Lane 1): Normal | (Default)  (Polarity - PHY1 Clock Lane): Normal
0x04,0x90,0x1D,0x00,0xF4, //  (config_soft_rst_n - PHY1): 0x0
// This is to set predefined (coarse) CSI output frequency
// CSI Phy 1 is 1500 Mbps/lane.
0x04,0x90,0x03,0x20,0x2F, // (Default) 
0x04,0x90,0x1D,0x00,0xF5, //  (config_soft_rst_n - PHY1): 0x1
0x04,0x90,0x03,0x32,0x30, //  (phy_Stdby_2): Put PHY2 in standby mode |  (phy_Stdby_3): Put PHY3 in standby mode
0x04,0x90,0x03,0x13,0x02, //  (CSI_OUT_EN): CSI output enabled
// Video Transmit Configuration for Serializer(s)
0x04,0x80,0x00,0x02,0x53, //  (VID_TX_EN_X): Enabled
0x04,0x82,0x00,0x02,0x53, //  (VID_TX_EN_X): Enabled

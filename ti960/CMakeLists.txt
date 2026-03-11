# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
if(NOT CROSS_COMPILE)
    project(ti960 VERSION 1.0 DESCRIPTION "TI960 Ser Des driver module" LANGUAGES C)
endif()

# Option for debug
option(SERDES_I2C_DEBUG            "Enable print Ser-Des register set value"              OFF)

set(LIB_NAME ti960)

add_subdirectory(include)
add_subdirectory(src)

add_library(${LIB_NAME} ${TI960_SRCS})
target_link_libraries(${LIB_NAME} PUBLIC ti960_api)
target_link_libraries(${LIB_NAME} PRIVATE ipu_utils vied_legacy io_aux)

set(CSF_SERDES_MODULES JETSON TI960_EVM HKR_AIC)
set(CSF_SERDES_MODULE HKR_AIC CACHE STRING "TI960 Module to build for")
set_property(CACHE CSF_SERDES_MODULE PROPERTY STRINGS ${CSF_SERDES_MODULES})
if(NOT CSF_SERDES_MODULE IN_LIST CSF_SERDES_MODULES)
    message(FATAL_ERROR "CSF_SERDES_MODULE: ${CSF_SERDES_MODULE} not supported")
endif()

target_compile_definitions(${LIB_NAME} PUBLIC ${CSF_SERDES_MODULE})
message("CSF_SERDES_MODEL: ${CSF_SERDES_MODULE} selected")

if(SERDES_I2C_DEBUG)
    target_compile_definitions(${LIB_NAME} PRIVATE -DSERDES_I2C_DEBUG)
endif()
message("SERDES_I2C_DEBUG: ${SERDES_I2C_DEBUG}")

install(TARGETS ${LIB_NAME} DESTINATION lib)

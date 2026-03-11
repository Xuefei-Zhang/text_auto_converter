# SPDX-License-Identifier: Apache-2.0

set(LIB_NAME ti960_api)

add_library(${LIB_NAME} INTERFACE)
target_include_directories(${LIB_NAME} INTERFACE ${CMAKE_CURRENT_LIST_DIR})

cmake_minimum_required(VERSION 3.17)

project(JDistributer)


set(HIREDIS_HEADER ${CMAKE_CURRENT_SOURCE_DIR}/third_party/hiredis)
set(HIREDIS_LIB ${CMAKE_CURRENT_SOURCE_DIR}/third_party/hiredis)
set(TEST_HIREDIS_LIB ${CMAKE_CURRENT_SOURCE_DIR}/third_party/hiredis)

option(BUILD_SHARED_LIBS "Build shared libraries" OFF)
OPTION(DISABLE_TESTS "If tests should be compiled or not" ON)
option(REDIS_PLUS_PLUS_BUILD_STATIC "Build static library" ON)
option(REDIS_PLUS_PLUS_BUILD_SHARED "Build shared library" OFF)
option(REDIS_PLUS_PLUS_BUILD_TEST "Build tests for redis++" OFF)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/third_party)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/third_party/hiredis)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/third_party/redis_plus_plus)

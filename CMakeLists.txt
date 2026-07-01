cmake_minimum_required(VERSION 3.21)
project(pyobs_fli LANGUAGES C CXX)

# --- Ensure we use the build environment Python ---
set(Python3_FIND_VIRTUALENV ONLY)
set(Python3_FIND_STRATEGY LOCATION)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)

# --- Paths ---
set(PYX_FILE "${CMAKE_CURRENT_SOURCE_DIR}/pyobs_fli/flidriver.pyx")
set(CXX_FILE "${CMAKE_CURRENT_BINARY_DIR}/flidriver.cpp")

# --- Get NumPy include dir ---
execute_process(
  COMMAND "${Python3_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
  OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

# --- Run Cython (C++ mode) ---
add_custom_command(
  OUTPUT ${CXX_FILE}
  COMMAND "${Python3_EXECUTABLE}" -m cython
          ${PYX_FILE}
          --output-file ${CXX_FILE}
          --cplus
          -I "${CMAKE_CURRENT_SOURCE_DIR}/pyobs_fli"
  DEPENDS ${PYX_FILE} "${CMAKE_CURRENT_SOURCE_DIR}/pyobs_fli/libfli.pxd"
  COMMENT "Running Cython on flidriver.pyx"
)

# --- Build libfli from source ---
set(LIBFLI_DIR "${CMAKE_CURRENT_SOURCE_DIR}/lib")
add_library(fli_static STATIC
  ${LIBFLI_DIR}/libfli.c
  ${LIBFLI_DIR}/libfli-camera.c
  ${LIBFLI_DIR}/libfli-camera-parport.c
  ${LIBFLI_DIR}/libfli-camera-usb.c
  ${LIBFLI_DIR}/libfli-filter-focuser.c
  ${LIBFLI_DIR}/libfli-mem.c
  ${LIBFLI_DIR}/libfli-raw.c
  ${LIBFLI_DIR}/unix/libfli-debug.c
  ${LIBFLI_DIR}/unix/libfli-serial.c
  ${LIBFLI_DIR}/unix/libfli-sys.c
  ${LIBFLI_DIR}/unix/libfli-usb.c
  ${LIBFLI_DIR}/unix/linux/libfli-parport.c
  ${LIBFLI_DIR}/unix/linux/libfli-usb-sys.c
)
target_include_directories(fli_static PUBLIC
  ${LIBFLI_DIR}
  ${LIBFLI_DIR}/unix
)
target_compile_options(fli_static PRIVATE -Wall -O2 -fPIC)

# --- Build extension module ---
add_library(flidriver MODULE ${CXX_FILE})
set_source_files_properties(${CXX_FILE} PROPERTIES LANGUAGE CXX)
target_include_directories(flidriver PRIVATE
  ${Python3_INCLUDE_DIRS}
  ${NUMPY_INCLUDE_DIR}
  ${LIBFLI_DIR}
)

# --- Correct Python module naming ---
execute_process(
  COMMAND "${Python3_EXECUTABLE}" -c
          "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"
  OUTPUT_VARIABLE PY_EXT_SUFFIX
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
set_target_properties(flidriver PROPERTIES
  PREFIX ""
  OUTPUT_NAME "flidriver"
  SUFFIX "${PY_EXT_SUFFIX}"
  POSITION_INDEPENDENT_CODE ON
)
message(STATUS "ext: ${PY_EXT_SUFFIX}")

# --- Link ---
find_library(CFITSIO_LIB cfitsio REQUIRED)
target_link_libraries(flidriver PRIVATE fli_static ${CFITSIO_LIB})

# --- Install into package ---
install(TARGETS flidriver
  LIBRARY DESTINATION ${SKBUILD_PROJECT_NAME}
)

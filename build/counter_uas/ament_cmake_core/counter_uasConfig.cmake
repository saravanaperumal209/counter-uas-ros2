# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_counter_uas_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED counter_uas_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(counter_uas_FOUND FALSE)
  elseif(NOT counter_uas_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(counter_uas_FOUND FALSE)
  endif()
  return()
endif()
set(_counter_uas_CONFIG_INCLUDED TRUE)

# output package information
if(NOT counter_uas_FIND_QUIETLY)
  message(STATUS "Found counter_uas: 0.1.0 (${counter_uas_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'counter_uas' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT counter_uas_DEPRECATED_QUIET)
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(counter_uas_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${counter_uas_DIR}/${_extra}")
endforeach()

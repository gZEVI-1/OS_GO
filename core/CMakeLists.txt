cmake_minimum_required(VERSION 3.18)
project(go_engine)

# C++17 стандарт
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

execute_process(
    COMMAND python -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
    ERROR_QUIET
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(PYBIND11_CMAKE_DIR)
    list(APPEND CMAKE_PREFIX_PATH ${PYBIND11_CMAKE_DIR})
    message(STATUS "pybind11 CMake dir found: ${PYBIND11_CMAKE_DIR}")
endif()

# Находим Python и pybind11
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11  REQUIRED)



# Создаем модуль
pybind11_add_module(go_engine 
    bindings.cpp
    core.cpp
)

# Линкуем с Python
target_link_libraries(go_engine PRIVATE 
    pybind11::module
)

# Инклюд директории
target_include_directories(go_engine PRIVATE 
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${Python_INCLUDE_DIRS}
)

# Для Windows: устанавливаем суффикс .pyd вместо .dll
if(WIN32)
    set_target_properties(go_engine PROPERTIES SUFFIX ".pyd")
endif()

# Установка
install(TARGETS go_engine DESTINATION .)
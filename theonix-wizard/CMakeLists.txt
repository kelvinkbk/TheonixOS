cmake_minimum_required(VERSION 3.16)

project(theonix-wizard VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 COMPONENTS Core Gui Qml Quick REQUIRED)

qt_add_executable(theonix-wizard
    src/main.cpp
    src/qml.qrc
)

target_link_libraries(theonix-wizard PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
)

install(TARGETS theonix-wizard
    RUNTIME DESTINATION bin
)

# Also install the autostart desktop file
install(FILES org.theonix.Wizard.desktop
    DESTINATION /etc/xdg/autostart
)

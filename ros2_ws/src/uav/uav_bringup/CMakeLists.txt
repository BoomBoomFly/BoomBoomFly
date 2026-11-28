cmake_minimum_required(VERSION 3.8)
project(uav_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch DESTINATION share/${PROJECT_NAME}
  PATTERN "__pycache__" EXCLUDE)
install(DIRECTORY config DESTINATION share/${PROJECT_NAME})

# 所有启动场景统一使用 launch/uav.launch.py。

ament_package()

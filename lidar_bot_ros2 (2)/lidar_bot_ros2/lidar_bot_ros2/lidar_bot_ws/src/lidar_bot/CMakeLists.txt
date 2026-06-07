cmake_minimum_required(VERSION 3.8)
project(lidar_bot)

find_package(ament_cmake REQUIRED)

# Установить все файлы ресурсов
install(DIRECTORY
  config
  launch
  maps
  urdf
  worlds
  rviz
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

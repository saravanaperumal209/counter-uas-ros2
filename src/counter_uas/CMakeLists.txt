cmake_minimum_required(VERSION 3.8)
project(counter_uas)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)

install(PROGRAMS
  counter_uas/intruder_drone.py
  counter_uas/radar_detector.py
  counter_uas/threat_classifier.py
  counter_uas/interceptor_drone.py
  counter_uas/mission_controller.py 
  counter_uas/drone_visualizer.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch worlds config urdf
  DESTINATION share/${PROJECT_NAME}
)

install(FILES resource/counter_uas
  DESTINATION share/ament_index/resource_index/packages
)

ament_package()

cmake_minimum_required(VERSION 3.0.2)
project(qt_node)

# 查找 catkin 包
find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  std_msgs
  geometry_msgs
)

catkin_package()

## 声明头文件和库文件的位置
include_directories(
  ${catkin_INCLUDE_DIRS}  # ROS 相关的头文件目录
  QT/src/qt_node/src/untitled.py  # 将 src 目录添加到 include 路径中
)

include_directories(
  ${catkin_INCLUDE_DIRS}  # ROS 相关的头文件目录
  QT/src/qt_node/src/untitled2.py  # 将 src 目录添加到 include 路径中
)

## 安装 Python 脚本文件
# 将 src/qt_node.py 脚本安装到 ROS 的 bin 目录中
catkin_install_python(PROGRAMS
   src/qt_node.py  # 这里的路径是相对于 CMakeLists.txt 文件的路径
   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
 )

 catkin_install_python(PROGRAMS
   src/qt2_node.py  # 这里的路径是相对于 CMakeLists.txt 文件的路径
   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
 )

## 安装源代码目录
# 将 src 目录下的其他文件安装到 ROS 包的 share 目录下
install(DIRECTORY src/ DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/src)

# 安装其他可能需要的资源文件（例如 launch 文件等）
# install(FILES
#   # myfile1
#   # myfile2
#   DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
# )


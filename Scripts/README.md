# 脚本

## installation(安装)

### 无人机
 
#### px4-Micro-XRCE-DDS方案
安装脚本
安装脚本会安装

消息依赖[px4_msgs](https://github.com/PX4/px4_msgs/)

通信依赖: [Micro-XRCE-DDS-Agent](https://github.com/eProsima/Micro-XRCE-DDS-Agent)

视觉系统和dds的功能包[vision_to_dds](https://github.com/wanone111/vision_to_dds.git)

offboard模式功能包[offboard](https://github.com/BoomBoomFly/offboard_cpp.git)

ros2上下位机串口通信功能包[serial_driver_ros](https://github.com/BoomBoomFly/serial_driver_ros.git)

视觉系统所需功能包[librealsense](git clone -b v2.53.1 https://github.com/IntelRealSense/librealsense.git)

视觉系统所需依赖包[realsense-ros](git clone -b 4.0.4 https://github.com/IntelRealSense/realsense-ros.git)


其中Intel® RealSense™ SDK 2.0 (v2.54.1) 中已经明确说明版本不再支持 T265 
这里我们选择2.53.1 realsense-ros选择4.0.4

####


### 小车



## simulation(仿真)

仿真脚本

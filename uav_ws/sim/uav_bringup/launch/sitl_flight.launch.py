from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    control_config = (
        Path(get_package_share_directory('uav_control')) / 'config' / 'control.yaml'
    )
    mission_config = (
        Path(get_package_share_directory('uav_mission')) / 'config' / 'mission.yaml'
    )
    return LaunchDescription([
        Node(
            package='uav_control',
            executable='mavros_interface_node',
            name='mavros_interface',
            output='screen',
            parameters=[str(control_config)],
        ),
        Node(
            package='uav_mission',
            executable='mission_node',
            name='uav_mission',
            output='screen',
            parameters=[str(mission_config)],
        ),
    ])

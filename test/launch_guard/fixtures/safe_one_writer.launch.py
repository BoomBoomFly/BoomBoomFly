from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="offboard_cpp",
            executable="offboard_node",
            name="offboard_control_node",
        )
    ])

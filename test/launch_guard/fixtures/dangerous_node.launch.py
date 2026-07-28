from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="serial_driver",
            executable="serial_driver_node",
            name="serial_driver",
            parameters=["unsafe_params.yaml"],
        )
    ])

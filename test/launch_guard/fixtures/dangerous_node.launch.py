from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="mavros",
            executable="mavros_node",
            name="mavros",
            parameters=["unsafe_params.yaml"],
        )
    ])

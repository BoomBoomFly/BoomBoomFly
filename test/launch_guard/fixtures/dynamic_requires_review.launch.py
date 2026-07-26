from launch import LaunchDescription
from launch.actions import OpaqueFunction


def add_runtime_actions(context):
    return []


def generate_launch_description():
    return LaunchDescription([OpaqueFunction(function=add_runtime_actions)])

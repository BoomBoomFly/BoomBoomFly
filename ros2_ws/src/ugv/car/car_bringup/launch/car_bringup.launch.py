"""Start the FPGA bridge, mapping, video and optional Jetson vision."""
from pathlib import Path
from os import pathsep

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue


def start_slam(context):
    selected = LaunchConfiguration('slam_library_dir').perform(context)
    use_private = bool(selected and selected != 'system')
    if use_private:
        private = Path(selected).expanduser()
        libraries = ('libkartoSlamToolbox.so', 'libtoolbox_common.so')
        if not all((private / name).is_file() for name in libraries):
            raise RuntimeError(f'{private} must contain both {libraries[0]} and {libraries[1]}')
        library_dir = private.resolve()
        mode = 'private Karto recovery libraries'
    else:
        library_dir = Path(get_package_prefix('slam_toolbox')) / 'lib'
        mode = 'system slam_toolbox'

    overrides = {'qos_overrides./tf.publisher.depth': 1,
                 'map_file_name': ParameterValue('', value_type=str)}
    if not use_private:
        # Humble's ROS callback tests distance before Karto sees the scan.
        # A stationary car still needs fresh scan poses to start its mission.
        overrides['minimum_travel_distance'] = 0.0
    inherited = context.environment.get('LD_LIBRARY_PATH', '')
    library_path = pathsep.join(filter(None, (str(library_dir), inherited)))
    return [
        LogInfo(msg=f'Car mapping uses {mode} in {library_dir}'),
        Node(package='slam_toolbox', executable='async_slam_toolbox_node', name='slam_toolbox',
             output='screen', parameters=[LaunchConfiguration('global_slam_config'), overrides],
             additional_env={'LD_LIBRARY_PATH': library_path,
                             'RMW_FASTRTPS_PUBLICATION_MODE': EnvironmentVariable(
                                 'RMW_FASTRTPS_PUBLICATION_MODE', default_value='ASYNCHRONOUS')}),
    ]


def generate_launch_description():
    bringup = Path(get_package_share_directory('car_bringup'))
    navigation = Path(get_package_share_directory('car_navigation'))
    config = LaunchConfiguration('config_file')
    camera_info_file = LaunchConfiguration('camera_info_file')
    return LaunchDescription([
        DeclareLaunchArgument('config_file', default_value=str(bringup / 'config' / 'bringup.yaml')),
        DeclareLaunchArgument('global_slam_config', default_value=str(navigation / 'config' / 'global_slam.yaml')),
        DeclareLaunchArgument('slam_library_dir', default_value='',
                              description='Optional private SLAM library directory; empty uses system slam_toolbox'),
        DeclareLaunchArgument('global_map_enabled', default_value='true'),
        DeclareLaunchArgument('enable_bridge', default_value='true'),
        DeclareLaunchArgument('enable_video', default_value='true'),
        DeclareLaunchArgument('enable_camera_mount', default_value='true'),
        DeclareLaunchArgument('enable_command', default_value='true'),
        DeclareLaunchArgument('enable_mission', default_value='true'),
        DeclareLaunchArgument('enable_waypoint_mppi', default_value='true'),
        DeclareLaunchArgument('enable_vision', default_value='true'),
        DeclareLaunchArgument('enable_detector', default_value=LaunchConfiguration('enable_vision')),
        DeclareLaunchArgument('enable_vision_mission', default_value=LaunchConfiguration('enable_vision')),
        DeclareLaunchArgument('camera_info_file', default_value='',
                              description='Calibrated 640x360 CameraInfo YAML for visual ranging'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(
            str(bringup / 'launch' / 'car_camera_mount.launch.py')),
            condition=IfCondition(LaunchConfiguration('enable_camera_mount'))),
        Node(package='ugv_bridge', executable='ugv_bridge_node', name='ugv_bridge_node',
             condition=IfCondition(LaunchConfiguration('enable_bridge')),
             output='screen', parameters=[config, {'qos_overrides./tf.publisher.depth': 1}],
             additional_env={'RMW_FASTRTPS_PUBLICATION_MODE': EnvironmentVariable(
                 'RMW_FASTRTPS_PUBLICATION_MODE', default_value='ASYNCHRONOUS')}),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(navigation / 'launch' / 'mission_services.launch.py')),
            launch_arguments={name: LaunchConfiguration(name) for name in
                              ('config_file', 'enable_command', 'enable_mission', 'enable_waypoint_mppi')}.items()),
        Node(package='ugv_bridge', executable='robot_video_node', name='robot_video',
             condition=IfCondition(LaunchConfiguration('enable_video')),
             output='screen', parameters=[config]),
        Node(package='car_vision', executable='vision_node', name='vision_node',
             condition=IfCondition(LaunchConfiguration('enable_detector')),
             output='screen', parameters=[config]),
        Node(package='car_vision', executable='vision_mission.py', name='vision_mission',
             condition=IfCondition(LaunchConfiguration('enable_vision_mission')),
             output='screen', parameters=[config, {'camera_info_file': ParameterValue(camera_info_file, value_type=str)}]),
        OpaqueFunction(function=start_slam,
                       condition=IfCondition(LaunchConfiguration('global_map_enabled'))),
    ])

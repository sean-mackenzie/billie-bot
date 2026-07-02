from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    map_file = LaunchConfiguration('map')
    mock_lidar = LaunchConfiguration('mock_lidar')
    mock_hardware = LaunchConfiguration('mock_hardware')
    return LaunchDescription([
        DeclareLaunchArgument('map', default_value=''),
        DeclareLaunchArgument('mock_lidar', default_value='true'),
        DeclareLaunchArgument('mock_hardware', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_bringup'), 'launch', 'drive.launch.py'
            ])),
            launch_arguments={'mock_hardware': mock_hardware}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_bringup'), 'launch', 'lidar.launch.py'
            ])),
            launch_arguments={'mock_lidar': mock_lidar}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_navigation'), 'launch', 'localization_amcl.launch.py'
            ])),
            launch_arguments={'map': map_file}.items(),
        ),
    ])

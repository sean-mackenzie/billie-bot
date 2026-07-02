from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mock_hardware = LaunchConfiguration('mock_hardware')
    mock_lidar = LaunchConfiguration('mock_lidar')
    return LaunchDescription([
        DeclareLaunchArgument('mock_hardware', default_value='true'),
        DeclareLaunchArgument('mock_lidar', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_bringup'), 'launch', 'drive.launch.py'
            ])),
            launch_arguments={'mock_hardware': mock_hardware}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_navigation'), 'launch', 'slam.launch.py'
            ])),
            launch_arguments={'mock_lidar': mock_lidar}.items(),
        ),
    ])

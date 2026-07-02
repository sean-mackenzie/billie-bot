from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mock_hardware = LaunchConfiguration('mock_hardware')
    port = LaunchConfiguration('port')
    return LaunchDescription([
        DeclareLaunchArgument('mock_hardware', default_value='true'),
        DeclareLaunchArgument('port', default_value='/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('billiebot_description'), 'launch', 'description.launch.py'
        ]))),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('billiebot_safety'), 'launch', 'safety.launch.py'
        ]))),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_control'), 'launch', 'drive.launch.py'
            ])),
            launch_arguments={'mock_hardware': mock_hardware, 'port': port}.items(),
        ),
    ])

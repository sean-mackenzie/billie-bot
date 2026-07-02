from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mock_lidar = LaunchConfiguration('mock_lidar')
    serial_port = LaunchConfiguration('serial_port')
    return LaunchDescription([
        DeclareLaunchArgument('mock_lidar', default_value='true'),
        DeclareLaunchArgument('serial_port', default_value='/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller-if00-port0'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_navigation'), 'launch', 'lidar.launch.py'
            ])),
            launch_arguments={'mock_lidar': mock_lidar, 'serial_port': serial_port}.items(),
        ),
    ])

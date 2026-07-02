from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    port = LaunchConfiguration('port')
    baudrate = LaunchConfiguration('baudrate')
    mock_hardware = LaunchConfiguration('mock_hardware')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('billiebot_control'), 'config', 'base_driver.yaml'
            ]),
        ),
        DeclareLaunchArgument('port', default_value='/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0'),
        DeclareLaunchArgument('baudrate', default_value='57600'),
        DeclareLaunchArgument('mock_hardware', default_value='false'),
        DeclareLaunchArgument('cmd_vel_topic', default_value='/cmd_vel_safe'),
        Node(
            package='billiebot_control',
            executable='diff_drive_base',
            name='diff_drive_base',
            output='screen',
            parameters=[
                params_file,
                {
                    'port': port,
                    'baudrate': ParameterValue(baudrate, value_type=int),
                    'mock_hardware': ParameterValue(mock_hardware, value_type=bool),
                    'cmd_vel_topic': cmd_vel_topic,
                },
            ],
        ),
    ])

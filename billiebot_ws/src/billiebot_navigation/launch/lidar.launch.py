from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    mock_lidar = LaunchConfiguration('mock_lidar')
    serial_port = LaunchConfiguration('serial_port')
    serial_baudrate = LaunchConfiguration('serial_baudrate')
    frame_id = LaunchConfiguration('frame_id')
    return LaunchDescription([
        DeclareLaunchArgument('mock_lidar', default_value='true'),
        DeclareLaunchArgument('serial_port', default_value='/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller-if00-port0'),
        DeclareLaunchArgument('serial_baudrate', default_value='115200'),
        DeclareLaunchArgument('frame_id', default_value='laser_frame'),
        Node(
            package='billiebot_navigation',
            executable='mock_lidar_node',
            name='mock_lidar_node',
            output='screen',
            parameters=[{'frame_id': frame_id}],
            condition=IfCondition(mock_lidar),
        ),
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_node',
            output='screen',
            parameters=[{
                'serial_port': serial_port,
                'serial_baudrate': ParameterValue(serial_baudrate, value_type=int),
                'frame_id': frame_id,
                'inverted': False,
                'angle_compensate': True,
            }],
            condition=UnlessCondition(mock_lidar),
        ),
    ])

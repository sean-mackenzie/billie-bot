from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    database_path = LaunchConfiguration('database_path')
    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('billiebot_logging'), 'config', 'logging.yaml'
            ]),
        ),
        DeclareLaunchArgument('database_path', default_value='~/.billiebot/billiebot_events.sqlite3'),
        Node(
            package='billiebot_logging',
            executable='event_logger_node',
            name='event_logger_node',
            output='screen',
            parameters=[params_file, {'database_path': database_path}],
        ),
    ])

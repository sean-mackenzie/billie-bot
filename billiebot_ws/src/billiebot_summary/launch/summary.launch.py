from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    database_path = LaunchConfiguration('database_path')
    date = LaunchConfiguration('date')
    output_path = LaunchConfiguration('output_path')
    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('billiebot_summary'), 'config', 'summary.yaml'
            ]),
        ),
        DeclareLaunchArgument('database_path', default_value='~/.billiebot/billiebot_events.sqlite3'),
        DeclareLaunchArgument('date', default_value=''),
        DeclareLaunchArgument('output_path', default_value='~/.billiebot/summaries'),
        Node(
            package='billiebot_summary',
            executable='daily_summary_node',
            name='daily_summary_node',
            output='screen',
            parameters=[
                params_file,
                {'database_path': database_path, 'date': date, 'output_path': output_path},
            ],
        ),
    ])

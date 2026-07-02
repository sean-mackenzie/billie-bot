from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    database_path = LaunchConfiguration('database_path')
    date = LaunchConfiguration('date')
    output_path = LaunchConfiguration('output_path')
    return LaunchDescription([
        DeclareLaunchArgument('database_path', default_value='~/.billiebot/billiebot_events.sqlite3'),
        DeclareLaunchArgument('date', default_value=''),
        DeclareLaunchArgument('output_path', default_value='~/.billiebot/summaries'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_summary'), 'launch', 'summary.launch.py'
            ])),
            launch_arguments={
                'database_path': database_path,
                'date': date,
                'output_path': output_path,
            }.items(),
        ),
    ])

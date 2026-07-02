from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    database_path = LaunchConfiguration('database_path')
    return LaunchDescription([
        DeclareLaunchArgument('database_path', default_value='~/.billiebot/billiebot_events.sqlite3'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_logging'), 'launch', 'logging.launch.py'
            ])),
            launch_arguments={'database_path': database_path}.items(),
        ),
    ])

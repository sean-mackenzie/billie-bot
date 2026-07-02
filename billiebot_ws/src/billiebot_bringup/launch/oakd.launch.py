from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mock_camera = LaunchConfiguration('mock_camera')
    return LaunchDescription([
        DeclareLaunchArgument('mock_camera', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_perception'), 'launch', 'oakd.launch.py'
            ])),
            launch_arguments={'mock_camera': mock_camera}.items(),
        ),
    ])

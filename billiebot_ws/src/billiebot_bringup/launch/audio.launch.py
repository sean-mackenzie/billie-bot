from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_audio_device = LaunchConfiguration('use_audio_device')
    mock_publish_events = LaunchConfiguration('mock_publish_events')
    return LaunchDescription([
        DeclareLaunchArgument('use_audio_device', default_value='false'),
        DeclareLaunchArgument('mock_publish_events', default_value='false'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_audio'), 'launch', 'audio.launch.py'
            ])),
            launch_arguments={
                'use_audio_device': use_audio_device,
                'mock_publish_events': mock_publish_events,
            }.items(),
        ),
    ])

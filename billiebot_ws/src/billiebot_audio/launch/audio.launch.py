from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    use_audio_device = LaunchConfiguration('use_audio_device')
    mock_publish_events = LaunchConfiguration('mock_publish_events')
    audio_device = LaunchConfiguration('audio_device')

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('billiebot_audio'), 'config', 'audio.yaml'
            ]),
        ),
        DeclareLaunchArgument('use_audio_device', default_value='false'),
        DeclareLaunchArgument('mock_publish_events', default_value='false'),
        DeclareLaunchArgument('audio_device', default_value='default'),
        Node(
            package='billiebot_audio',
            executable='audio_event_node',
            name='audio_event_node',
            output='screen',
            parameters=[
                params_file,
                {
                    'use_audio_device': ParameterValue(use_audio_device, value_type=bool),
                    'mock_publish_events': ParameterValue(mock_publish_events, value_type=bool),
                    'audio_device': audio_device,
                },
            ],
        ),
    ])

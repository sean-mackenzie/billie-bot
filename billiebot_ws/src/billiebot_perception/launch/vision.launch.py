from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    mock_camera = LaunchConfiguration('mock_camera')
    detector_backend = LaunchConfiguration('detector_backend')
    mock_publish_detection = LaunchConfiguration('mock_publish_detection')

    return LaunchDescription([
        DeclareLaunchArgument('mock_camera', default_value='true'),
        DeclareLaunchArgument('detector_backend', default_value='mock'),
        DeclareLaunchArgument('mock_publish_detection', default_value='false'),
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('billiebot_perception'), 'config', 'perception.yaml'
            ]),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_perception'), 'launch', 'oakd.launch.py'
            ])),
            launch_arguments={'mock_camera': mock_camera, 'params_file': params_file}.items(),
        ),
        Node(
            package='billiebot_perception',
            executable='billie_detector_node',
            name='billie_detector_node',
            output='screen',
            parameters=[
                params_file,
                {
                    'detector_backend': detector_backend,
                    'mock_publish_detection': ParameterValue(mock_publish_detection, value_type=bool),
                },
            ],
        ),
        Node(
            package='billiebot_perception',
            executable='visual_state_node',
            name='visual_state_node',
            output='screen',
            parameters=[params_file],
        ),
    ])

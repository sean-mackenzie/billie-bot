from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mock_camera = LaunchConfiguration('mock_camera')
    detector_backend = LaunchConfiguration('detector_backend')
    mock_publish_detection = LaunchConfiguration('mock_publish_detection')
    return LaunchDescription([
        DeclareLaunchArgument('mock_camera', default_value='true'),
        DeclareLaunchArgument('detector_backend', default_value='mock'),
        DeclareLaunchArgument('mock_publish_detection', default_value='false'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_perception'), 'launch', 'vision.launch.py'
            ])),
            launch_arguments={
                'mock_camera': mock_camera,
                'detector_backend': detector_backend,
                'mock_publish_detection': mock_publish_detection,
            }.items(),
        ),
    ])

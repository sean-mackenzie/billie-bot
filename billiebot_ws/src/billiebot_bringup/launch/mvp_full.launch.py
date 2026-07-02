from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mock_hardware = LaunchConfiguration('mock_hardware')
    mock_lidar = LaunchConfiguration('mock_lidar')
    mock_camera = LaunchConfiguration('mock_camera')
    detector_backend = LaunchConfiguration('detector_backend')
    mock_publish_detection = LaunchConfiguration('mock_publish_detection')
    mock_audio_events = LaunchConfiguration('mock_audio_events')
    database_path = LaunchConfiguration('database_path')

    return LaunchDescription([
        DeclareLaunchArgument('mock_hardware', default_value='true'),
        DeclareLaunchArgument('mock_lidar', default_value='true'),
        DeclareLaunchArgument('mock_camera', default_value='true'),
        DeclareLaunchArgument('detector_backend', default_value='mock'),
        DeclareLaunchArgument('mock_publish_detection', default_value='false'),
        DeclareLaunchArgument('mock_audio_events', default_value='false'),
        DeclareLaunchArgument('database_path', default_value='~/.billiebot/billiebot_events.sqlite3'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_bringup'), 'launch', 'slam.launch.py'
            ])),
            launch_arguments={'mock_hardware': mock_hardware, 'mock_lidar': mock_lidar}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_bringup'), 'launch', 'nav2.launch.py'
            ])),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_bringup'), 'launch', 'vision.launch.py'
            ])),
            launch_arguments={
                'mock_camera': mock_camera,
                'detector_backend': detector_backend,
                'mock_publish_detection': mock_publish_detection,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_bringup'), 'launch', 'audio.launch.py'
            ])),
            launch_arguments={'mock_publish_events': mock_audio_events}.items(),
        ),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('billiebot_bringup'), 'launch', 'state.launch.py'
        ]))),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('billiebot_bringup'), 'launch', 'logging.launch.py'
            ])),
            launch_arguments={'database_path': database_path}.items(),
        ),
    ])

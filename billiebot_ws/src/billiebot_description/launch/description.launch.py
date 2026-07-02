from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_lidar = LaunchConfiguration('use_lidar')
    use_camera = LaunchConfiguration('use_camera')
    use_imu = LaunchConfiguration('use_imu')
    use_mic = LaunchConfiguration('use_mic')

    xacro_file = PathJoinSubstitution([
        FindPackageShare('billiebot_description'),
        'urdf',
        'billiebot.urdf.xacro',
    ])

    robot_description = Command([
        'xacro ',
        xacro_file,
        ' use_lidar:=', use_lidar,
        ' use_camera:=', use_camera,
        ' use_imu:=', use_imu,
        ' use_mic:=', use_mic,
    ])

    return LaunchDescription([
        DeclareLaunchArgument('use_lidar', default_value='true'),
        DeclareLaunchArgument('use_camera', default_value='true'),
        DeclareLaunchArgument('use_imu', default_value='true'),
        DeclareLaunchArgument('use_mic', default_value='true'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description}],
        ),
    ])

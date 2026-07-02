from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('billiebot_state'), 'config', 'state.yaml'
            ]),
        ),
        Node(
            package='billiebot_state',
            executable='billie_state_estimator',
            name='billie_state_estimator',
            output='screen',
            parameters=[params_file],
        ),
    ])

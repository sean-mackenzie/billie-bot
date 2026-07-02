from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mock_camera = LaunchConfiguration('mock_camera')
    params_file = LaunchConfiguration('params_file')

    return LaunchDescription([
        DeclareLaunchArgument('mock_camera', default_value='true'),
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('billiebot_perception'), 'config', 'perception.yaml'
            ]),
        ),
        Node(
            package='billiebot_perception',
            executable='mock_camera_node',
            name='mock_camera_node',
            output='screen',
            parameters=[params_file],
            condition=IfCondition(mock_camera),
        ),
        Node(
            package='depthai_ros_driver',
            executable='camera',
            name='oak',
            output='screen',
            parameters=[{'camera': {'i_nn_type': 'none'}}],
            condition=UnlessCondition(mock_camera),
        ),
    ])

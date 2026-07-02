from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    waypoints_file = LaunchConfiguration('waypoints_file')
    return LaunchDescription([
        DeclareLaunchArgument(
            'waypoints_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('billiebot_navigation'), 'config', 'search_waypoints.yaml'
            ]),
        ),
        Node(
            package='billiebot_navigation',
            executable='waypoint_search_node',
            name='waypoint_search_node',
            output='screen',
            parameters=[{'waypoints_file': waypoints_file}],
        ),
    ])

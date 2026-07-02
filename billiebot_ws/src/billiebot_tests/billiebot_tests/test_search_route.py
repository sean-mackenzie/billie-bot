#!/usr/bin/env python3
"""
Test Objective:
  Load sample search waypoints and send them to Nav2 waypoint following.
Required Hardware:
  Nav2 waypoint follower with map/SLAM and clear test area.
Setup:
  Launch Nav2 and ensure configured waypoints are reachable.
Launch:
  ros2 launch billiebot_bringup nav2.launch.py map:=/path/to/map.yaml
Verification:
  ros2 run billiebot_tests test_search_route --ros-args -p waypoints_file:=/path/to/search_waypoints.yaml
Pass Criteria:
  FollowWaypoints accepts the route and returns a result.
Fail Criteria:
  Waypoint file is invalid, action server is missing, or route times out.
Notes:
  This is deterministic route following, not Behavior AI.
"""
import math

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import FollowWaypoints
from rclpy.action import ActionClient
from rclpy.node import Node

try:
    import yaml
except ImportError:
    yaml = None

from billiebot_tests.ros_test_utils import fail, pass_msg


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_search_route')
    node.declare_parameter('waypoints_file', '')
    node.declare_parameter('timeout_sec', 60.0)
    if yaml is None:
        fail('PyYAML is required')
    path = node.get_parameter('waypoints_file').value
    if not path:
        fail('Set waypoints_file to the search_waypoints.yaml path')
    with open(path, 'r', encoding='utf-8') as handle:
        data = yaml.safe_load(handle) or {}
    poses = []
    for item in data.get('waypoints', []):
        pose = PoseStamped()
        pose.header.frame_id = data.get('frame_id', 'map')
        pose.header.stamp = node.get_clock().now().to_msg()
        pose.pose.position.x = float(item.get('x', 0.0))
        pose.pose.position.y = float(item.get('y', 0.0))
        yaw = float(item.get('yaw', 0.0))
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        poses.append(pose)
    if not poses:
        fail('No waypoints loaded')
    client = ActionClient(node, FollowWaypoints, 'follow_waypoints')
    if not client.wait_for_server(timeout_sec=8.0):
        fail('follow_waypoints action server unavailable')
    goal = FollowWaypoints.Goal()
    goal.poses = poses
    send_future = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, send_future, timeout_sec=5.0)
    handle = send_future.result()
    if handle is None or not handle.accepted:
        fail('Search route rejected')
    result_future = handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future, timeout_sec=float(node.get_parameter('timeout_sec').value))
    if result_future.result() is None:
        fail('Search route timed out')
    pass_msg(f'search route result status={result_future.result().status}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

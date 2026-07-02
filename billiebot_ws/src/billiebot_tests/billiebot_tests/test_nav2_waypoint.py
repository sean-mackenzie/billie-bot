#!/usr/bin/env python3
"""
Test Objective:
  Send a simple Nav2 navigation goal and verify action acceptance/result.
Required Hardware:
  Nav2 localization stack with map/SLAM and clear test area.
Setup:
  Launch Nav2 and set a valid initial pose.
Launch:
  ros2 launch billiebot_bringup nav2.launch.py map:=/path/to/map.yaml
Verification:
  ros2 run billiebot_tests test_nav2_waypoint
Pass Criteria:
  NavigateToPose action accepts the goal and returns a result.
Fail Criteria:
  Action server is unavailable, rejects the goal, or times out.
Notes:
  The default goal is small; override goal_x/goal_y for your apartment map.
"""
import math

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node

from billiebot_tests.ros_test_utils import fail, pass_msg


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_nav2_waypoint')
    node.declare_parameter('goal_x', 0.25)
    node.declare_parameter('goal_y', 0.0)
    node.declare_parameter('goal_yaw', 0.0)
    node.declare_parameter('timeout_sec', 20.0)
    client = ActionClient(node, NavigateToPose, 'navigate_to_pose')
    if not client.wait_for_server(timeout_sec=8.0):
        fail('navigate_to_pose action server unavailable')
    goal = NavigateToPose.Goal()
    goal.pose = PoseStamped()
    goal.pose.header.frame_id = 'map'
    goal.pose.header.stamp = node.get_clock().now().to_msg()
    goal.pose.pose.position.x = float(node.get_parameter('goal_x').value)
    goal.pose.pose.position.y = float(node.get_parameter('goal_y').value)
    yaw = float(node.get_parameter('goal_yaw').value)
    goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
    goal.pose.pose.orientation.w = math.cos(yaw / 2.0)
    send_future = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, send_future, timeout_sec=5.0)
    handle = send_future.result()
    if handle is None or not handle.accepted:
        fail('Nav2 goal rejected or no response')
    result_future = handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future, timeout_sec=float(node.get_parameter('timeout_sec').value))
    if result_future.result() is None:
        fail('Nav2 goal result timed out')
    pass_msg(f'Nav2 goal completed with status={result_future.result().status}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

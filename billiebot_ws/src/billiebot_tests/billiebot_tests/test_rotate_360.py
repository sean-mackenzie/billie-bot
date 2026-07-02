#!/usr/bin/env python3
"""
Test Objective:
  Command approximately 360 degrees of rotation and report odometry yaw change.
Required Hardware:
  Drive base for hardware mode; mock drive for CI.
Setup:
  Place orientation tape on the floor. Launch drive and safety.
Launch:
  ros2 launch billiebot_bringup drive.launch.py mock_hardware:=false
Verification:
  ros2 run billiebot_tests test_rotate_360
Pass Criteria:
  Accumulated odometry yaw reaches at least 5.5 rad and manual heading is close.
Fail Criteria:
  /odom is missing or yaw accumulation is too small.
Notes:
  Use this to tune wheel separation and motor/encoder signs.
"""
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

from billiebot_tests.ros_test_utils import fail, pass_msg, publish_twist_for, wait_for_message, yaw_from_quat


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_rotate_360')
    node.declare_parameter('cmd_vel_topic', '/cmd_vel')
    node.declare_parameter('angular_speed_rps', 0.35)
    node.declare_parameter('target_rad', 2.0 * math.pi)
    node.declare_parameter('max_duration_sec', 24.0)
    pub = node.create_publisher(Twist, node.get_parameter('cmd_vel_topic').value, 10)
    first = wait_for_message(node, Odometry, '/odom', 5.0)
    if first is None:
        fail('No /odom before rotate test')
    last_yaw = yaw_from_quat(first.pose.pose.orientation)
    accumulated = 0.0
    deadline = time.monotonic() + float(node.get_parameter('max_duration_sec').value)
    while rclpy.ok() and time.monotonic() < deadline and accumulated < float(node.get_parameter('target_rad').value):
        publish_twist_for(node, pub, 0.0, float(node.get_parameter('angular_speed_rps').value), 0.2)
        msg = wait_for_message(node, Odometry, '/odom', 1.0)
        if msg is None:
            continue
        yaw = yaw_from_quat(msg.pose.pose.orientation)
        accumulated += abs(math.atan2(math.sin(yaw - last_yaw), math.cos(yaw - last_yaw)))
        last_yaw = yaw
    pub.publish(Twist())
    if accumulated < 5.5:
        fail(f'Yaw accumulation too small: {accumulated:.3f} rad')
    pass_msg(f'rotate odometry yaw accumulation={accumulated:.3f} rad; compare with manual heading')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

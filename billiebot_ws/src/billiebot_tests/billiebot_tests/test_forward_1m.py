#!/usr/bin/env python3
"""
Test Objective:
  Command the robot forward approximately 1 meter and report odometry distance.
Required Hardware:
  Drive base for hardware mode; mock drive for CI.
Setup:
  Mark a 1 m straight line on the floor. Launch drive and safety.
Launch:
  ros2 launch billiebot_bringup drive.launch.py mock_hardware:=false
Verification:
  ros2 run billiebot_tests test_forward_1m
Pass Criteria:
  Odometry reports at least 0.8 m and the manual measured travel is acceptably close.
Fail Criteria:
  /odom is missing or odometry distance is too small.
Notes:
  Compare the printed odometry estimate against tape-measure distance for calibration.
"""
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

from billiebot_tests.ros_test_utils import fail, odom_distance, pass_msg, publish_twist_for, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_forward_1m')
    node.declare_parameter('cmd_vel_topic', '/cmd_vel')
    node.declare_parameter('speed_mps', 0.10)
    node.declare_parameter('target_m', 1.0)
    node.declare_parameter('max_duration_sec', 14.0)
    pub = node.create_publisher(Twist, node.get_parameter('cmd_vel_topic').value, 10)
    start = wait_for_message(node, Odometry, '/odom', 5.0)
    if start is None:
        fail('No /odom before forward test')
    deadline = time.monotonic() + float(node.get_parameter('max_duration_sec').value)
    latest = start
    while rclpy.ok() and time.monotonic() < deadline:
        publish_twist_for(node, pub, float(node.get_parameter('speed_mps').value), 0.0, 0.2)
        msg = wait_for_message(node, Odometry, '/odom', 1.0)
        if msg is not None:
            latest = msg
        if odom_distance(start, latest) >= float(node.get_parameter('target_m').value):
            break
    pub.publish(Twist())
    distance = odom_distance(start, latest)
    if distance < 0.8 * float(node.get_parameter('target_m').value):
        fail(f'Forward odometry distance too small: {distance:.3f} m')
    pass_msg(f'forward odometry distance={distance:.3f} m; compare with manual measurement')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

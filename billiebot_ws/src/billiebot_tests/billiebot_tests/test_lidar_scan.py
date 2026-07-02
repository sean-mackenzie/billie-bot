#!/usr/bin/env python3
"""
Test Objective:
  Verify /scan publishes non-empty LaserScan data at a reasonable frequency.
Required Hardware:
  RPLidar A1 for hardware mode; none if mock_lidar:=true.
Setup:
  Launch lidar.
Launch:
  ros2 launch billiebot_bringup lidar.launch.py mock_lidar:=false
Verification:
  ros2 run billiebot_tests test_lidar_scan
Pass Criteria:
  Multiple /scan messages arrive, ranges are non-empty, and measured Hz exceeds min_hz.
Fail Criteria:
  /scan is missing, empty, or too slow.
Notes:
  Mock lidar should publish at about 5 Hz.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

from billiebot_tests.ros_test_utils import collect_messages, fail, pass_msg


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_lidar_scan')
    node.declare_parameter('timeout_sec', 5.0)
    node.declare_parameter('min_hz', 1.0)
    timeout = float(node.get_parameter('timeout_sec').value)
    msgs = collect_messages(node, LaserScan, '/scan', timeout, 10)
    if len(msgs) < 2:
        fail('Fewer than two /scan messages received')
    if not msgs[-1].ranges:
        fail('/scan ranges are empty')
    hz = (len(msgs) - 1) / timeout
    if hz < float(node.get_parameter('min_hz').value):
        fail(f'/scan frequency too low: {hz:.2f} Hz')
    pass_msg(f'/scan received with {len(msgs[-1].ranges)} ranges at approx {hz:.2f} Hz')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

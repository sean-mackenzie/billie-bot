#!/usr/bin/env python3
"""
Test Objective:
  Verify encoder-derived odometry changes when wheels are moved or commanded.
Required Hardware:
  Differential-drive base with Arduino encoder bridge; mock drive mode is acceptable for CI.
Setup:
  Launch drive. Rotate wheels manually or command low-speed motion.
Launch:
  ros2 launch billiebot_bringup drive.launch.py mock_hardware:=false
Verification:
  ros2 run billiebot_tests test_encoder_counts
Pass Criteria:
  /odom changes by more than min_distance_m within the observation window.
Fail Criteria:
  /odom is absent or remains unchanged.
Notes:
  This validates ROS-level encoder odometry, not raw microcontroller tick values.
"""
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node

from billiebot_tests.ros_test_utils import collect_messages, fail, odom_distance, pass_msg


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_encoder_counts')
    node.declare_parameter('timeout_sec', 6.0)
    node.declare_parameter('min_distance_m', 0.005)
    msgs = collect_messages(node, Odometry, '/odom', float(node.get_parameter('timeout_sec').value), 20)
    if len(msgs) < 2:
        fail('Need at least two /odom messages')
    distance = odom_distance(msgs[0], msgs[-1])
    if distance < float(node.get_parameter('min_distance_m').value):
        fail(f'/odom did not change enough: {distance:.4f} m')
    pass_msg(f'encoder/odom changed by {distance:.3f} m')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Test Objective:
  Publish safe /cmd_vel commands and verify /odom changes.
Required Hardware:
  Drive base for hardware mode; mock drive for CI.
Setup:
  Launch drive and safety.
Launch:
  ros2 launch billiebot_bringup drive.launch.py mock_hardware:=true
Verification:
  ros2 run billiebot_tests test_teleop_drive
Pass Criteria:
  /odom changes after a short forward command.
Fail Criteria:
  /odom is missing or unchanged.
Notes:
  For hardware, keep the command speed low and ensure a clear path.
"""
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

from billiebot_tests.ros_test_utils import fail, odom_distance, pass_msg, publish_twist_for, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_teleop_drive')
    node.declare_parameter('cmd_vel_topic', '/cmd_vel')
    node.declare_parameter('speed_mps', 0.08)
    node.declare_parameter('duration_sec', 2.0)
    pub = node.create_publisher(Twist, node.get_parameter('cmd_vel_topic').value, 10)
    before = wait_for_message(node, Odometry, '/odom', 5.0)
    if before is None:
        fail('No /odom before drive command')
    publish_twist_for(node, pub, float(node.get_parameter('speed_mps').value), 0.0, float(node.get_parameter('duration_sec').value))
    after = wait_for_message(node, Odometry, '/odom', 5.0)
    if after is None:
        fail('No /odom after drive command')
    distance = odom_distance(before, after)
    if distance < 0.02:
        fail(f'Expected /odom movement, got {distance:.3f} m')
    pass_msg(f'teleop drive odom movement={distance:.3f} m')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

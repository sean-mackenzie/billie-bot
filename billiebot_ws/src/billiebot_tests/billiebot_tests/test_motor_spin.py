#!/usr/bin/env python3
"""
Test Objective:
  Send low-speed forward/reverse motor commands through the normal command path.
Required Hardware:
  Differential-drive base for hardware mode; none if drive is launched with mock_hardware:=true.
Setup:
  Put the robot on blocks for hardware mode. Launch drive and safety.
Launch:
  ros2 launch billiebot_bringup drive.launch.py mock_hardware:=false
Verification:
  ros2 run billiebot_tests test_motor_spin
Pass Criteria:
  Commands are published without error; if verify_odom:=true, /odom changes.
Fail Criteria:
  /odom is missing when requested, or command publication fails.
Notes:
  Use very low speeds and keep the robot clear of people and pets.
"""
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

from billiebot_tests.ros_test_utils import fail, odom_distance, pass_msg, publish_twist_for, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_motor_spin')
    node.declare_parameter('cmd_vel_topic', '/cmd_vel')
    node.declare_parameter('speed_mps', 0.06)
    node.declare_parameter('duration_sec', 1.0)
    node.declare_parameter('verify_odom', False)
    pub = node.create_publisher(Twist, node.get_parameter('cmd_vel_topic').value, 10)
    before = None
    if bool(node.get_parameter('verify_odom').value):
        before = wait_for_message(node, Odometry, '/odom', 5.0)
        if before is None:
            fail('No /odom message received before motor spin test')
    speed = float(node.get_parameter('speed_mps').value)
    duration = float(node.get_parameter('duration_sec').value)
    publish_twist_for(node, pub, speed, 0.0, duration)
    publish_twist_for(node, pub, -speed, 0.0, duration)
    if before is not None:
        after = wait_for_message(node, Odometry, '/odom', 5.0)
        if after is None or odom_distance(before, after) <= 0.005:
            fail('Expected /odom to change during motor spin test')
    pass_msg('motor spin command sequence completed')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

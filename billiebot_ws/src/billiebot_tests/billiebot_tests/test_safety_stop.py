#!/usr/bin/env python3
"""
Test Objective:
  Verify safety supervisor clamps unsafe velocity commands and honors software E-stop.
Required Hardware:
  None.
Setup:
  Launch safety supervisor.
Launch:
  ros2 launch billiebot_safety safety.launch.py
Verification:
  ros2 run billiebot_tests test_safety_stop
Pass Criteria:
  /cmd_vel_safe is clamped and becomes zero after E-stop service call.
Fail Criteria:
  Safe command is missing, unclamped, or E-stop does not stop output.
Notes:
  This test does not require the motor controller.
"""
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_srvs.srv import SetBool

from billiebot_tests.ros_test_utils import fail, pass_msg, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_safety_stop')
    node.declare_parameter('input_topic', '/cmd_vel')
    node.declare_parameter('output_topic', '/cmd_vel_safe')
    node.declare_parameter('max_linear_velocity', 0.25)
    node.declare_parameter('max_angular_velocity', 0.9)
    pub = node.create_publisher(Twist, node.get_parameter('input_topic').value, 10)
    unsafe = Twist()
    unsafe.linear.x = 9.0
    unsafe.angular.z = 9.0
    for _ in range(6):
        pub.publish(unsafe)
        rclpy.spin_once(node, timeout_sec=0.05)
    safe = wait_for_message(node, Twist, node.get_parameter('output_topic').value, 4.0)
    if safe is None:
        fail('No /cmd_vel_safe message received')
    if abs(safe.linear.x) > float(node.get_parameter('max_linear_velocity').value) + 1e-6:
        fail(f'Linear velocity was not clamped: {safe.linear.x}')
    if abs(safe.angular.z) > float(node.get_parameter('max_angular_velocity').value) + 1e-6:
        fail(f'Angular velocity was not clamped: {safe.angular.z}')
    client = node.create_client(SetBool, '/billiebot/set_estop')
    if not client.wait_for_service(timeout_sec=4.0):
        fail('/billiebot/set_estop service unavailable')
    req = SetBool.Request()
    req.data = True
    future = client.call_async(req)
    rclpy.spin_until_future_complete(node, future, timeout_sec=4.0)
    stopped = wait_for_message(node, Twist, node.get_parameter('output_topic').value, 4.0)
    req.data = False
    clear_future = client.call_async(req)
    rclpy.spin_until_future_complete(node, clear_future, timeout_sec=2.0)
    if stopped is None or abs(stopped.linear.x) > 1e-6 or abs(stopped.angular.z) > 1e-6:
        fail('E-stop did not force /cmd_vel_safe to zero')
    pass_msg('safety clamp and E-stop behavior verified')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

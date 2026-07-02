#!/usr/bin/env python3
"""
Test Objective:
  Verify /billie/detections publishes BillieDetectionArray messages.
Required Hardware:
  OAK-D Lite for hardware detection; none with mock camera/detector.
Setup:
  Launch vision. For CI, use mock_publish_detection:=true.
Launch:
  ros2 launch billiebot_bringup vision.launch.py mock_camera:=true detector_backend:=mock mock_publish_detection:=true
Verification:
  ros2 run billiebot_tests test_billie_visual_detection --ros-args -p require_detection:=true
Pass Criteria:
  /billie/detections publishes; if require_detection:=true, at least one detection is present.
Fail Criteria:
  Topic is missing or required detections are absent.
Notes:
  Mock detector publishes no detections by default unless explicitly enabled.
"""
import rclpy
from rclpy.node import Node

from billiebot_msgs.msg import BillieDetectionArray
from billiebot_tests.ros_test_utils import fail, pass_msg, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_billie_visual_detection')
    node.declare_parameter('timeout_sec', 8.0)
    node.declare_parameter('require_detection', False)
    msg = wait_for_message(node, BillieDetectionArray, '/billie/detections', float(node.get_parameter('timeout_sec').value))
    if msg is None:
        fail('No /billie/detections message received')
    if bool(node.get_parameter('require_detection').value) and not msg.detections:
        fail('Detection array was received but contains no detections')
    pass_msg(f'/billie/detections received with {len(msg.detections)} detections')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

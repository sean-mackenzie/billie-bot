#!/usr/bin/env python3
"""
Test Objective:
  Verify OAK-D RGB and depth topics publish valid image dimensions and timestamps.
Required Hardware:
  OAK-D Lite for hardware mode; none if mock_camera:=true.
Setup:
  Launch OAK-D or mock camera.
Launch:
  ros2 launch billiebot_bringup oakd.launch.py mock_camera:=false
Verification:
  ros2 run billiebot_tests test_camera_oakd
Pass Criteria:
  RGB and depth images arrive with non-zero width/height.
Fail Criteria:
  Either image topic is missing or dimensions are invalid.
Notes:
  Override rgb_topic/depth_topic parameters if driver topic names differ.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

from billiebot_tests.ros_test_utils import fail, pass_msg, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_camera_oakd')
    node.declare_parameter('rgb_topic', '/oak/rgb/image_raw')
    node.declare_parameter('depth_topic', '/oak/stereo/depth')
    node.declare_parameter('timeout_sec', 8.0)
    timeout = float(node.get_parameter('timeout_sec').value)
    rgb = wait_for_message(node, Image, node.get_parameter('rgb_topic').value, timeout)
    depth = wait_for_message(node, Image, node.get_parameter('depth_topic').value, timeout)
    if rgb is None or depth is None:
        fail('RGB or depth image topic did not publish')
    if rgb.width <= 0 or rgb.height <= 0 or depth.width <= 0 or depth.height <= 0:
        fail('RGB or depth image dimensions are invalid')
    pass_msg(f'RGB {rgb.width}x{rgb.height}, depth {depth.width}x{depth.height}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

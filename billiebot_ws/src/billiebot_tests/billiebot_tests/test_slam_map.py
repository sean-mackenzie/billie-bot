#!/usr/bin/env python3
"""
Test Objective:
  Verify /map publishes after SLAM launch.
Required Hardware:
  Lidar and drive for hardware mode; mock lidar/drive can exercise topic plumbing.
Setup:
  Launch SLAM.
Launch:
  ros2 launch billiebot_bringup slam.launch.py mock_lidar:=true mock_hardware:=true
Verification:
  ros2 run billiebot_tests test_slam_map
Pass Criteria:
  /map publishes an OccupancyGrid with non-zero dimensions and data.
Fail Criteria:
  /map is missing or empty.
Notes:
  A useful real map still requires moving the robot through the apartment.
"""
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node

from billiebot_tests.ros_test_utils import fail, pass_msg, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_slam_map')
    node.declare_parameter('timeout_sec', 12.0)
    msg = wait_for_message(node, OccupancyGrid, '/map', float(node.get_parameter('timeout_sec').value))
    if msg is None:
        fail('No /map message received')
    if msg.info.width == 0 or msg.info.height == 0 or not msg.data:
        fail('/map OccupancyGrid is empty')
    pass_msg(f'/map dimensions={msg.info.width}x{msg.info.height}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Test Objective:
  Verify AMCL pose output and map->odom TF availability.
Required Hardware:
  Map, lidar, and odometry for hardware localization.
Setup:
  Launch AMCL with a valid map.
Launch:
  ros2 launch billiebot_bringup amcl.launch.py map:=/path/to/map.yaml
Verification:
  ros2 run billiebot_tests test_localization_amcl
Pass Criteria:
  /amcl_pose publishes and map->odom transform is available.
Fail Criteria:
  AMCL pose or TF lookup times out.
Notes:
  Set an initial pose in RViz if AMCL has not converged.
"""
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener

from billiebot_tests.ros_test_utils import fail, pass_msg, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_localization_amcl')
    node.declare_parameter('timeout_sec', 10.0)
    pose = wait_for_message(node, PoseWithCovarianceStamped, '/amcl_pose', float(node.get_parameter('timeout_sec').value))
    if pose is None:
        fail('No /amcl_pose message received')
    buffer = Buffer()
    TransformListener(buffer, node)
    ok = False
    for _ in range(30):
        rclpy.spin_once(node, timeout_sec=0.1)
        try:
            buffer.lookup_transform('map', 'odom', rclpy.time.Time())
            ok = True
            break
        except TransformException:
            pass
    if not ok:
        fail('map -> odom TF is not available')
    pass_msg('/amcl_pose and map->odom TF are available')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

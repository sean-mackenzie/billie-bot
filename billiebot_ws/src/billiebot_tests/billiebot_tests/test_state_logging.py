#!/usr/bin/env python3
"""
Test Objective:
  Publish sample Billie state observations and verify SQLite events are written.
Required Hardware:
  None.
Setup:
  Launch logging with a known database_path.
Launch:
  ros2 launch billiebot_bringup logging.launch.py database_path:=/tmp/billiebot_test.sqlite3
Verification:
  ros2 run billiebot_tests test_state_logging --ros-args -p database_path:=/tmp/billiebot_test.sqlite3
Pass Criteria:
  /billie/events_logged reports success and the events table row count increases.
Fail Criteria:
  Logger status is missing/failed or SQLite row is absent.
Notes:
  This test assumes the logger node is already running.
"""
import os
import time

import rclpy
from rclpy.node import Node

from billiebot_msgs.msg import BillieStateObservation, EventLogStatus
from billiebot_tests.ros_test_utils import fail, pass_msg, sqlite_count, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_state_logging')
    node.declare_parameter('database_path', '/tmp/billiebot_test.sqlite3')
    node.declare_parameter('timeout_sec', 6.0)
    database_path = os.path.expanduser(str(node.get_parameter('database_path').value))
    before = 0
    if os.path.exists(database_path):
        before = sqlite_count(database_path, "SELECT COUNT(*) FROM events WHERE state_label = 'seen'")
    pub = node.create_publisher(BillieStateObservation, '/billie/state', 10)
    msg = BillieStateObservation()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.state_label = 'seen'
    msg.confidence = 0.95
    msg.evidence_source = 'test_state_logging'
    msg.robot_pose.pose.orientation.w = 1.0
    msg.estimated_billie_pose.pose.orientation.w = 1.0
    for _ in range(8):
        pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.05)
    status = wait_for_message(node, EventLogStatus, '/billie/events_logged', float(node.get_parameter('timeout_sec').value))
    if status is None or not status.success:
        fail('No successful /billie/events_logged status received')
    deadline = time.monotonic() + 3.0
    after = before
    while time.monotonic() < deadline:
        if os.path.exists(database_path):
            after = sqlite_count(database_path, "SELECT COUNT(*) FROM events WHERE state_label = 'seen'")
            if after > before:
                break
        time.sleep(0.1)
    if after <= before:
        fail('No new state observation row found in SQLite')
    pass_msg(f'SQLite state rows increased from {before} to {after}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

import math
import sqlite3
import sys
import time
from typing import List, Optional

import rclpy
from geometry_msgs.msg import Twist


def fail(message: str):
    print(f'FAIL: {message}', file=sys.stderr)
    raise SystemExit(1)


def pass_msg(message: str):
    print(f'PASS: {message}')


def wait_for_message(node, msg_type, topic: str, timeout_sec: float = 5.0):
    received = {'msg': None}

    def callback(msg):
        received['msg'] = msg

    subscription = node.create_subscription(msg_type, topic, callback, 10)
    deadline = time.monotonic() + timeout_sec
    while rclpy.ok() and time.monotonic() < deadline and received['msg'] is None:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_subscription(subscription)
    return received['msg']


def collect_messages(node, msg_type, topic: str, timeout_sec: float = 5.0, max_count: int = 20) -> List:
    messages = []

    def callback(msg):
        messages.append(msg)

    subscription = node.create_subscription(msg_type, topic, callback, 10)
    deadline = time.monotonic() + timeout_sec
    while rclpy.ok() and time.monotonic() < deadline and len(messages) < max_count:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_subscription(subscription)
    return messages


def publish_twist_for(node, publisher, linear: float, angular: float, duration_sec: float, rate_hz: float = 10.0):
    msg = Twist()
    msg.linear.x = float(linear)
    msg.angular.z = float(angular)
    period = 1.0 / rate_hz
    deadline = time.monotonic() + duration_sec
    while rclpy.ok() and time.monotonic() < deadline:
        publisher.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.01)
        time.sleep(period)
    publisher.publish(Twist())


def yaw_from_quat(q) -> float:
    return math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z)


def odom_xy(msg):
    return msg.pose.pose.position.x, msg.pose.pose.position.y


def odom_distance(a, b) -> float:
    ax, ay = odom_xy(a)
    bx, by = odom_xy(b)
    return math.hypot(bx - ax, by - ay)


def sqlite_count(database_path: str, sql: str, values: tuple = ()) -> int:
    conn = sqlite3.connect(database_path)
    try:
        row = conn.execute(sql, values).fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    finally:
        conn.close()


def optional_param(node, name: str, default):
    node.declare_parameter(name, default)
    return node.get_parameter(name).value

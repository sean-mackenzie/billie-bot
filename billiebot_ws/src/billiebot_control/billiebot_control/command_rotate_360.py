#!/usr/bin/env python3
import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node


class Rotate360(Node):
    def __init__(self):
        super().__init__('command_rotate_360')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('angular_speed_rps', 0.35)
        self.declare_parameter('target_rad', 2.0 * math.pi)
        self.cmd_pub = self.create_publisher(Twist, self.get_parameter('cmd_vel_topic').value, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.last_yaw = None
        self.accumulated = 0.0
        self.timer = self.create_timer(0.1, self.tick)

    @staticmethod
    def yaw_from_odom(msg):
        q = msg.pose.pose.orientation
        return math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z)

    def odom_callback(self, msg):
        yaw = self.yaw_from_odom(msg)
        if self.last_yaw is not None:
            delta = math.atan2(math.sin(yaw - self.last_yaw), math.cos(yaw - self.last_yaw))
            self.accumulated += abs(delta)
        self.last_yaw = yaw

    def tick(self):
        msg = Twist()
        if self.accumulated < float(self.get_parameter('target_rad').value):
            msg.angular.z = float(self.get_parameter('angular_speed_rps').value)
        self.cmd_pub.publish(msg)
        if self.accumulated >= float(self.get_parameter('target_rad').value):
            self.get_logger().info(f'Rotate calibration complete: odom yaw change={self.accumulated:.3f} rad')
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = Rotate360()
    rclpy.spin(node)


if __name__ == '__main__':
    main()

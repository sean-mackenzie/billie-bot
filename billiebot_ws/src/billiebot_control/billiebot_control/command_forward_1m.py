#!/usr/bin/env python3
import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node


class ForwardOneMeter(Node):
    def __init__(self):
        super().__init__('command_forward_1m')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('speed_mps', 0.10)
        self.declare_parameter('distance_m', 1.0)
        self.declare_parameter('odom_topic', '/odom')
        self.cmd_pub = self.create_publisher(Twist, self.get_parameter('cmd_vel_topic').value, 10)
        self.odom_sub = self.create_subscription(
            Odometry, self.get_parameter('odom_topic').value, self.odom_callback, 10
        )
        self.start_xy = None
        self.latest_xy = None
        self.done = False
        self.timer = self.create_timer(0.1, self.tick)

    def odom_callback(self, msg):
        self.latest_xy = (msg.pose.pose.position.x, msg.pose.pose.position.y)
        if self.start_xy is None:
            self.start_xy = self.latest_xy

    def travelled(self):
        if self.start_xy is None or self.latest_xy is None:
            return 0.0
        return math.hypot(self.latest_xy[0] - self.start_xy[0], self.latest_xy[1] - self.start_xy[1])

    def tick(self):
        target = float(self.get_parameter('distance_m').value)
        speed = float(self.get_parameter('speed_mps').value)
        msg = Twist()
        if self.travelled() < target:
            msg.linear.x = speed
        else:
            self.done = True
        self.cmd_pub.publish(msg)
        if self.done:
            self.get_logger().info(f'Forward calibration complete: odom distance={self.travelled():.3f} m')
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = ForwardOneMeter()
    rclpy.spin(node)


if __name__ == '__main__':
    main()

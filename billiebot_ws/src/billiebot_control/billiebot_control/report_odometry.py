#!/usr/bin/env python3
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node


class ReportOdometry(Node):
    def __init__(self):
        super().__init__('report_odometry')
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

    def odom_callback(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.get_logger().info(
            f'odom position=({p.x:.3f}, {p.y:.3f}, {p.z:.3f}) orientation_z={q.z:.3f} w={q.w:.3f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = ReportOdometry()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

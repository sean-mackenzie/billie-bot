#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class MockLidarNode(Node):
    def __init__(self):
        super().__init__('mock_lidar_node')
        self.declare_parameter('frame_id', 'laser_frame')
        self.declare_parameter('publish_rate_hz', 5.0)
        self.declare_parameter('range_m', 2.5)
        self.pub = self.create_publisher(LaserScan, '/scan', 10)
        self.timer = self.create_timer(1.0 / float(self.get_parameter('publish_rate_hz').value), self.publish_scan)
        self.get_logger().warn('Publishing mock /scan data')

    def publish_scan(self):
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = str(self.get_parameter('frame_id').value)
        msg.angle_min = -math.pi
        msg.angle_max = math.pi
        msg.angle_increment = math.radians(1.0)
        msg.time_increment = 0.0
        msg.scan_time = 0.2
        msg.range_min = 0.15
        msg.range_max = 12.0
        samples = int((msg.angle_max - msg.angle_min) / msg.angle_increment)
        msg.ranges = [float(self.get_parameter('range_m').value)] * samples
        msg.intensities = [0.0] * samples
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MockLidarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

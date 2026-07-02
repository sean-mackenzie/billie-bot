#!/usr/bin/env python3
import struct

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image


class MockCameraNode(Node):
    def __init__(self):
        super().__init__('mock_camera_node')
        self.declare_parameter('rgb_topic', '/oak/rgb/image_raw')
        self.declare_parameter('depth_topic', '/oak/stereo/depth')
        self.declare_parameter('camera_info_topic', '/oak/rgb/camera_info')
        self.declare_parameter('frame_id', 'oak_camera_optical_frame')
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 400)
        self.declare_parameter('publish_rate_hz', 10.0)
        self.declare_parameter('depth_m', 1.5)

        self.width = int(self.get_parameter('width').value)
        self.height = int(self.get_parameter('height').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        self.depth_m = float(self.get_parameter('depth_m').value)
        self.rgb_pub = self.create_publisher(Image, str(self.get_parameter('rgb_topic').value), 10)
        self.depth_pub = self.create_publisher(Image, str(self.get_parameter('depth_topic').value), 10)
        self.info_pub = self.create_publisher(CameraInfo, str(self.get_parameter('camera_info_topic').value), 10)
        self.timer = self.create_timer(1.0 / float(self.get_parameter('publish_rate_hz').value), self.publish)
        self.get_logger().warn('Publishing mock OAK-D RGB/depth frames')

    def publish(self):
        stamp = self.get_clock().now().to_msg()
        rgb = Image()
        rgb.header.stamp = stamp
        rgb.header.frame_id = self.frame_id
        rgb.height = self.height
        rgb.width = self.width
        rgb.encoding = 'rgb8'
        rgb.is_bigendian = False
        rgb.step = self.width * 3
        rgb.data = bytes([32, 32, 32]) * self.width * self.height

        depth = Image()
        depth.header = rgb.header
        depth.height = self.height
        depth.width = self.width
        depth.encoding = '32FC1'
        depth.is_bigendian = False
        depth.step = self.width * 4
        depth.data = struct.pack('<f', self.depth_m) * self.width * self.height

        info = CameraInfo()
        info.header = rgb.header
        info.height = self.height
        info.width = self.width
        info.k = [525.0, 0.0, self.width / 2.0, 0.0, 525.0, self.height / 2.0, 0.0, 0.0, 1.0]

        self.rgb_pub.publish(rgb)
        self.depth_pub.publish(depth)
        self.info_pub.publish(info)


def main(args=None):
    rclpy.init(args=args)
    node = MockCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

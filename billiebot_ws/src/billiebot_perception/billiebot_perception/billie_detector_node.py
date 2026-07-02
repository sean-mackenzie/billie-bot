#!/usr/bin/env python3
import math
import struct
from typing import Optional

import rclpy
from billiebot_msgs.msg import BillieDetection, BillieDetectionArray
from rclpy.node import Node
from sensor_msgs.msg import Image

try:
    from cv_bridge import CvBridge
except ImportError:  # pragma: no cover
    CvBridge = None


class BillieDetectorNode(Node):
    def __init__(self):
        super().__init__('billie_detector_node')
        self.declare_parameter('image_topic', '/oak/rgb/image_raw')
        self.declare_parameter('depth_topic', '/oak/stereo/depth')
        self.declare_parameter('detector_backend', 'mock')
        self.declare_parameter('model_path', '')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('dog_class_name', 'dog')
        self.declare_parameter('dog_class_id', 16)
        self.declare_parameter('publish_debug_image', False)
        self.declare_parameter('mock_publish_detection', False)
        self.declare_parameter('mock_confidence', 0.9)
        self.declare_parameter('camera_frame', 'oak_camera_frame')
        self.declare_parameter('horizontal_fov_rad', 1.204)

        self.backend = str(self.get_parameter('detector_backend').value)
        self.bridge = CvBridge() if CvBridge is not None else None
        self.latest_depth: Optional[Image] = None
        self.latest_width = 0
        self.latest_height = 0

        self.create_subscription(Image, str(self.get_parameter('image_topic').value), self.image_callback, 10)
        self.create_subscription(Image, str(self.get_parameter('depth_topic').value), self.depth_callback, 10)
        self.detection_pub = self.create_publisher(BillieDetectionArray, '/billie/detections', 10)
        self.debug_pub = self.create_publisher(Image, '/billie/detections/debug_image', 10)

        if self.backend == 'ultralytics':
            self.get_logger().warn('Ultralytics backend is a configured extension point; install/model wiring is TODO')
        elif self.backend == 'opencv':
            self.get_logger().warn('OpenCV backend is a lightweight placeholder and publishes only high-confidence heuristic detections')
        else:
            self.get_logger().info('Mock detector active')

    def depth_callback(self, msg: Image):
        self.latest_depth = msg

    def estimate_depth_at_center(self, width: int, height: int) -> float:
        if self.latest_depth is None:
            return float('nan')
        depth = self.latest_depth
        if depth.width == 0 or depth.height == 0:
            return float('nan')
        cx = min(depth.width - 1, max(0, int(width / 2)))
        cy = min(depth.height - 1, max(0, int(height / 2)))
        if depth.encoding == '32FC1':
            offset = cy * depth.step + cx * 4
            if offset + 4 <= len(depth.data):
                value = struct.unpack_from('<f', bytes(depth.data), offset)[0]
                return value if math.isfinite(value) and value > 0.0 else float('nan')
        if depth.encoding in ('16UC1', 'mono16'):
            offset = cy * depth.step + cx * 2
            if offset + 2 <= len(depth.data):
                return struct.unpack_from('<H', bytes(depth.data), offset)[0] / 1000.0
        return float('nan')

    def make_detection(self, stamp, width: int, height: int, confidence: float) -> BillieDetection:
        range_m = self.estimate_depth_at_center(width, height)
        bbox_width = width * 0.25
        bbox_height = height * 0.35
        bbox_x = (width - bbox_width) / 2.0
        bbox_y = (height - bbox_height) / 2.0
        bearing = 0.0

        det = BillieDetection()
        det.header.stamp = stamp
        det.header.frame_id = str(self.get_parameter('camera_frame').value)
        det.detector_name = self.backend
        det.class_label = str(self.get_parameter('dog_class_name').value)
        det.confidence = float(confidence)
        det.bbox_x = float(bbox_x)
        det.bbox_y = float(bbox_y)
        det.bbox_width = float(bbox_width)
        det.bbox_height = float(bbox_height)
        det.range_m = float(range_m) if math.isfinite(range_m) else -1.0
        det.bearing_rad = bearing
        det.estimated_pose.header = det.header
        if math.isfinite(range_m):
            det.estimated_pose.pose.position.x = range_m
        det.estimated_pose.pose.orientation.w = 1.0
        det.is_billie_candidate = True
        return det

    def image_callback(self, msg: Image):
        self.latest_width = msg.width
        self.latest_height = msg.height
        arr = BillieDetectionArray()
        arr.header = msg.header

        threshold = float(self.get_parameter('confidence_threshold').value)
        if self.backend == 'mock':
            if bool(self.get_parameter('mock_publish_detection').value):
                confidence = float(self.get_parameter('mock_confidence').value)
                if confidence >= threshold:
                    arr.detections.append(self.make_detection(msg.header.stamp, msg.width, msg.height, confidence))
        elif self.backend == 'opencv':
            self.get_logger().debug('OpenCV placeholder backend received frame; no dog model configured')
        elif self.backend == 'ultralytics':
            self.get_logger().debug('Ultralytics backend selected but no model runner is active')
        else:
            self.get_logger().warning(f'Unknown detector_backend={self.backend}; publishing no detections')

        self.detection_pub.publish(arr)
        if bool(self.get_parameter('publish_debug_image').value):
            self.debug_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = BillieDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

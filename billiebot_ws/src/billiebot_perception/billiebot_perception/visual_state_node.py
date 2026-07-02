#!/usr/bin/env python3
import math

import rclpy
from billiebot_msgs.msg import BillieDetectionArray, BillieStateObservation
from rclpy.node import Node


class VisualStateNode(Node):
    def __init__(self):
        super().__init__('visual_state_node')
        self.declare_parameter('detection_topic', '/billie/detections')
        self.declare_parameter('output_topic', '/billie/visual_state')
        self.declare_parameter('detection_timeout_sec', 2.0)
        self.declare_parameter('moving_bearing_threshold_rad', 0.08)
        self.declare_parameter('stationary_duration_sec', 20.0)
        self.declare_parameter('minimum_confidence', 0.5)

        self.last_detection_time = None
        self.last_bearing = None
        self.stationary_since = None
        self.current_state = 'unknown'
        self.current_confidence = 0.0

        self.create_subscription(
            BillieDetectionArray,
            str(self.get_parameter('detection_topic').value),
            self.detections_callback,
            10,
        )
        self.pub = self.create_publisher(
            BillieStateObservation,
            str(self.get_parameter('output_topic').value),
            10,
        )
        self.timer = self.create_timer(0.5, self.publish_state)

    def detections_callback(self, msg: BillieDetectionArray):
        candidates = [
            d for d in msg.detections
            if d.is_billie_candidate and d.confidence >= float(self.get_parameter('minimum_confidence').value)
        ]
        if not candidates:
            return
        det = max(candidates, key=lambda item: item.confidence)
        now = self.get_clock().now()
        moving_threshold = float(self.get_parameter('moving_bearing_threshold_rad').value)

        if self.last_bearing is not None and abs(det.bearing_rad - self.last_bearing) > moving_threshold:
            self.current_state = 'moving'
            self.stationary_since = None
        else:
            if self.stationary_since is None:
                self.stationary_since = now
                self.current_state = 'seen'
            elif (now - self.stationary_since).nanoseconds * 1e-9 >= float(
                self.get_parameter('stationary_duration_sec').value
            ):
                self.current_state = 'sleeping'
            else:
                self.current_state = 'seen'

        self.current_confidence = det.confidence
        self.last_bearing = det.bearing_rad
        self.last_detection_time = now

    def publish_state(self):
        now = self.get_clock().now()
        if self.last_detection_time is None:
            state = 'unknown'
            confidence = 0.0
        else:
            age = (now - self.last_detection_time).nanoseconds * 1e-9
            if age > float(self.get_parameter('detection_timeout_sec').value):
                state = 'unknown'
                confidence = 0.0
            else:
                state = self.current_state
                confidence = self.current_confidence

        msg = BillieStateObservation()
        msg.header.stamp = now.to_msg()
        msg.state_label = state
        msg.confidence = float(confidence) if math.isfinite(confidence) else 0.0
        msg.evidence_source = 'vision'
        msg.robot_pose.pose.orientation.w = 1.0
        msg.estimated_billie_pose.pose.orientation.w = 1.0
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = VisualStateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

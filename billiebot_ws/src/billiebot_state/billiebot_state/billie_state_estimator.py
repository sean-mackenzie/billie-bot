#!/usr/bin/env python3
import math

import rclpy
from billiebot_msgs.msg import AudioEvent, BillieDetectionArray, BillieStateObservation
from nav_msgs.msg import Odometry
from rclpy.node import Node


class BillieStateEstimator(Node):
    def __init__(self):
        super().__init__('billie_state_estimator')
        self.declare_parameter('detection_topic', '/billie/detections')
        self.declare_parameter('audio_topic', '/billie/audio_events')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('state_topic', '/billie/state')
        self.declare_parameter('detection_timeout', 5.0)
        self.declare_parameter('sleep_stationary_duration', 30.0)
        self.declare_parameter('movement_threshold', 0.10)
        self.declare_parameter('audio_event_timeout', 4.0)
        self.declare_parameter('minimum_confidence', 0.5)
        self.declare_parameter('publish_rate_hz', 2.0)

        self.latest_detection = None
        self.latest_detection_time = None
        self.previous_detection_pose = None
        self.stationary_since = None
        self.latest_audio = None
        self.latest_audio_time = None
        self.latest_robot_pose = None

        self.create_subscription(
            BillieDetectionArray,
            str(self.get_parameter('detection_topic').value),
            self.detections_callback,
            10,
        )
        self.create_subscription(
            AudioEvent,
            str(self.get_parameter('audio_topic').value),
            self.audio_callback,
            10,
        )
        self.create_subscription(Odometry, str(self.get_parameter('odom_topic').value), self.odom_callback, 10)
        self.pub = self.create_publisher(
            BillieStateObservation,
            str(self.get_parameter('state_topic').value),
            10,
        )
        self.timer = self.create_timer(1.0 / float(self.get_parameter('publish_rate_hz').value), self.publish_state)

    def detections_callback(self, msg: BillieDetectionArray):
        min_conf = float(self.get_parameter('minimum_confidence').value)
        candidates = [d for d in msg.detections if d.is_billie_candidate and d.confidence >= min_conf]
        if not candidates:
            return
        self.latest_detection = max(candidates, key=lambda det: det.confidence)
        self.latest_detection_time = self.get_clock().now()

    def audio_callback(self, msg: AudioEvent):
        self.latest_audio = msg
        self.latest_audio_time = self.get_clock().now()

    def odom_callback(self, msg: Odometry):
        self.latest_robot_pose = msg.pose.pose

    @staticmethod
    def detection_motion(prev, cur) -> float:
        if prev is None or cur is None:
            return 0.0
        dx = cur.estimated_pose.pose.position.x - prev.estimated_pose.pose.position.x
        dy = cur.estimated_pose.pose.position.y - prev.estimated_pose.pose.position.y
        bearing_delta = abs(cur.bearing_rad - prev.bearing_rad)
        return max(math.hypot(dx, dy), bearing_delta)

    def classify_visual(self, now):
        if self.latest_detection is None or self.latest_detection_time is None:
            return 'not_seen', 0.2, 'no_visual_detection'
        age = (now - self.latest_detection_time).nanoseconds * 1e-9
        if age > float(self.get_parameter('detection_timeout').value):
            return 'not_seen', 0.4, 'visual_detection_timeout'

        motion = self.detection_motion(self.previous_detection_pose, self.latest_detection)
        self.previous_detection_pose = self.latest_detection
        if motion > float(self.get_parameter('movement_threshold').value):
            self.stationary_since = None
            return 'moving', self.latest_detection.confidence, 'visual_motion'

        if self.stationary_since is None:
            self.stationary_since = now
            return 'seen', self.latest_detection.confidence, 'visual_detection'

        stationary_age = (now - self.stationary_since).nanoseconds * 1e-9
        if stationary_age >= float(self.get_parameter('sleep_stationary_duration').value):
            return 'sleeping', min(1.0, self.latest_detection.confidence + 0.1), 'stable_visual_detection'
        return 'seen', self.latest_detection.confidence, 'visual_detection'

    def classify_audio(self, now):
        if self.latest_audio is None or self.latest_audio_time is None:
            return None
        age = (now - self.latest_audio_time).nanoseconds * 1e-9
        if age > float(self.get_parameter('audio_event_timeout').value):
            return None
        if self.latest_audio.event_type == 'bark':
            return 'barking', self.latest_audio.confidence, 'audio_bark'
        if self.latest_audio.event_type == 'loud_noise':
            return 'loud_noise', self.latest_audio.confidence, 'audio_loud_noise'
        return 'unknown', self.latest_audio.confidence, 'audio_unknown'

    def publish_state(self):
        now = self.get_clock().now()
        audio_state = self.classify_audio(now)
        if audio_state is not None and audio_state[0] in ('barking', 'loud_noise'):
            state, confidence, evidence = audio_state
        else:
            state, confidence, evidence = self.classify_visual(now)
            if audio_state is not None and audio_state[0] == 'unknown' and confidence < 0.6:
                state, confidence, evidence = 'unknown', 0.3, 'conflicting_or_low_confidence'

        msg = BillieStateObservation()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = 'map'
        msg.state_label = state
        msg.confidence = float(confidence)
        msg.evidence_source = evidence
        if self.latest_robot_pose is not None:
            msg.robot_pose.header.stamp = msg.header.stamp
            msg.robot_pose.header.frame_id = 'odom'
            msg.robot_pose.pose = self.latest_robot_pose
        else:
            msg.robot_pose.pose.orientation.w = 1.0
        if self.latest_detection is not None:
            msg.estimated_billie_pose = self.latest_detection.estimated_pose
        else:
            msg.estimated_billie_pose.pose.orientation.w = 1.0
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = BillieStateEstimator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

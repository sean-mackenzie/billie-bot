#!/usr/bin/env python3
import math
import time

import rclpy
from billiebot_msgs.msg import AudioEvent
from rclpy.node import Node
from std_msgs.msg import Float32

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None


class AudioEventNode(Node):
    def __init__(self):
        super().__init__('audio_event_node')
        self.declare_parameter('audio_device', 'default')
        self.declare_parameter('use_audio_device', False)
        self.declare_parameter('audio_level_topic', '/billiebot/audio_level_db')
        self.declare_parameter('sample_rate', 16000)
        self.declare_parameter('frame_size', 1024)
        self.declare_parameter('loudness_threshold_db', 68.0)
        self.declare_parameter('bark_classifier_mode', 'threshold')
        self.declare_parameter('minimum_event_duration', 0.15)
        self.declare_parameter('event_cooldown', 1.0)
        self.declare_parameter('mock_publish_events', False)
        self.declare_parameter('mock_event_type', 'bark')
        self.declare_parameter('mock_loudness_db', 82.0)
        self.declare_parameter('doa_rad', 0.0)

        self.pub = self.create_publisher(AudioEvent, '/billie/audio_events', 10)
        self.last_event_wall_time = 0.0
        self.above_threshold_since = None
        self.stream = None

        self.create_subscription(
            Float32,
            str(self.get_parameter('audio_level_topic').value),
            self.level_callback,
            10,
        )

        if bool(self.get_parameter('use_audio_device').value):
            self.start_audio_device()
        else:
            self.get_logger().info('Audio device capture disabled; using audio_level_topic/mock modes')

        self.timer = self.create_timer(0.2, self.mock_tick)

    def start_audio_device(self):
        if sd is None or np is None:
            self.get_logger().warn('sounddevice/numpy unavailable; ReSpeaker capture is disabled')
            return

        sample_rate = int(self.get_parameter('sample_rate').value)
        frame_size = int(self.get_parameter('frame_size').value)
        device = str(self.get_parameter('audio_device').value)

        def callback(indata, frames, _time_info, status):
            if status:
                self.get_logger().warning(f'audio input status: {status}')
            rms = float(np.sqrt(np.mean(np.square(indata)))) if frames else 0.0
            db = 20.0 * math.log10(max(rms, 1e-6)) + 100.0
            self.handle_loudness(db)

        try:
            self.stream = sd.InputStream(
                device=None if device == 'default' else device,
                channels=1,
                samplerate=sample_rate,
                blocksize=frame_size,
                callback=callback,
            )
            self.stream.start()
            self.get_logger().info(f'Audio capture started on device={device}')
        except Exception as exc:  # pragma: no cover - device-specific.
            self.get_logger().error(f'Could not start audio capture: {exc}')

    def level_callback(self, msg: Float32):
        self.handle_loudness(float(msg.data))

    def classify_event(self, loudness_db: float) -> str:
        mode = str(self.get_parameter('bark_classifier_mode').value)
        if mode == 'mock':
            return str(self.get_parameter('mock_event_type').value)
        if mode == 'model':
            self.get_logger().debug('Audio model mode selected but no local model is configured')
            return 'unknown'
        if loudness_db >= float(self.get_parameter('loudness_threshold_db').value) + 8.0:
            return 'bark'
        return 'loud_noise'

    def handle_loudness(self, loudness_db: float):
        threshold = float(self.get_parameter('loudness_threshold_db').value)
        now_ros = self.get_clock().now()
        now_wall = time.monotonic()
        if loudness_db >= threshold:
            if self.above_threshold_since is None:
                self.above_threshold_since = now_ros
            duration = (now_ros - self.above_threshold_since).nanoseconds * 1e-9
            if (
                duration >= float(self.get_parameter('minimum_event_duration').value)
                and now_wall - self.last_event_wall_time >= float(self.get_parameter('event_cooldown').value)
            ):
                self.publish_event(self.classify_event(loudness_db), loudness_db, duration)
                self.last_event_wall_time = now_wall
                self.above_threshold_since = None
        else:
            self.above_threshold_since = None

    def publish_event(self, event_type: str, loudness_db: float, duration_s: float):
        msg = AudioEvent()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'mic_link'
        msg.event_type = event_type if event_type in ('bark', 'loud_noise', 'unknown') else 'unknown'
        msg.confidence = 0.8 if msg.event_type != 'unknown' else 0.3
        msg.loudness_db = float(loudness_db)
        msg.duration_s = float(duration_s)
        msg.doa_rad = float(self.get_parameter('doa_rad').value)
        self.pub.publish(msg)
        self.get_logger().info(
            f'Audio event: type={msg.event_type} loudness={msg.loudness_db:.1f} dB duration={msg.duration_s:.2f}s'
        )

    def mock_tick(self):
        if not bool(self.get_parameter('mock_publish_events').value):
            return
        now = time.monotonic()
        cooldown = float(self.get_parameter('event_cooldown').value)
        if now - self.last_event_wall_time >= cooldown:
            self.publish_event(
                str(self.get_parameter('mock_event_type').value),
                float(self.get_parameter('mock_loudness_db').value),
                float(self.get_parameter('minimum_event_duration').value),
            )
            self.last_event_wall_time = now

    def destroy_node(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = AudioEventNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Test Objective:
  Verify audio node publishes events during clap/bark/loud-noise or injected mock loudness.
Required Hardware:
  ReSpeaker/XVF3800 for hardware mode; none with mock_inject:=true.
Setup:
  Launch audio node.
Launch:
  ros2 launch billiebot_bringup audio.launch.py
Verification:
  ros2 run billiebot_tests test_audio_event --ros-args -p mock_inject:=true
Pass Criteria:
  /billie/audio_events publishes an AudioEvent.
Fail Criteria:
  No event arrives before timeout.
Notes:
  mock_inject publishes loudness to /billiebot/audio_level_db.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

from billiebot_msgs.msg import AudioEvent
from billiebot_tests.ros_test_utils import fail, pass_msg, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_audio_event')
    node.declare_parameter('mock_inject', False)
    node.declare_parameter('audio_level_topic', '/billiebot/audio_level_db')
    node.declare_parameter('timeout_sec', 6.0)
    if bool(node.get_parameter('mock_inject').value):
        pub = node.create_publisher(Float32, node.get_parameter('audio_level_topic').value, 10)
        msg = Float32()
        msg.data = 90.0
        for _ in range(10):
            pub.publish(msg)
            rclpy.spin_once(node, timeout_sec=0.05)
    event = wait_for_message(node, AudioEvent, '/billie/audio_events', float(node.get_parameter('timeout_sec').value))
    if event is None:
        fail('No /billie/audio_events message received')
    pass_msg(f'audio event={event.event_type} loudness={event.loudness_db:.1f} dB')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

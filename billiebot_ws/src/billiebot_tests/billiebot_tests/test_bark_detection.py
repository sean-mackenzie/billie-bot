#!/usr/bin/env python3
"""
Test Objective:
  Verify bark/loud-noise event publication.
Required Hardware:
  ReSpeaker/XVF3800 for hardware mode; none with mock injection.
Setup:
  Launch audio node.
Launch:
  ros2 launch billiebot_bringup audio.launch.py
Verification:
  ros2 run billiebot_tests test_bark_detection --ros-args -p mock_inject:=true
Pass Criteria:
  /billie/audio_events publishes bark, loud_noise, or unknown after the stimulus.
Fail Criteria:
  No audio event arrives before timeout.
Notes:
  Threshold mode classifies very loud injected levels as bark.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

from billiebot_msgs.msg import AudioEvent
from billiebot_tests.ros_test_utils import fail, pass_msg, wait_for_message


def main(args=None):
    rclpy.init(args=args)
    node = Node('test_bark_detection')
    node.declare_parameter('mock_inject', False)
    node.declare_parameter('audio_level_topic', '/billiebot/audio_level_db')
    node.declare_parameter('timeout_sec', 8.0)
    if bool(node.get_parameter('mock_inject').value):
        pub = node.create_publisher(Float32, node.get_parameter('audio_level_topic').value, 10)
        loud = Float32()
        loud.data = 92.0
        for _ in range(12):
            pub.publish(loud)
            rclpy.spin_once(node, timeout_sec=0.05)
    event = wait_for_message(node, AudioEvent, '/billie/audio_events', float(node.get_parameter('timeout_sec').value))
    if event is None:
        fail('No bark/loud-noise audio event received')
    if event.event_type not in ('bark', 'loud_noise', 'unknown'):
        fail(f'Unexpected audio event type: {event.event_type}')
    pass_msg(f'audio event type={event.event_type}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

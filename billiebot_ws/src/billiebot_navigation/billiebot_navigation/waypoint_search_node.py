#!/usr/bin/env python3
import math
from typing import List

import rclpy
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import FollowWaypoints
from rclpy.action import ActionClient
from rclpy.node import Node

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def quaternion_from_yaw(yaw: float) -> Quaternion:
    q = Quaternion()
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


class WaypointSearchNode(Node):
    def __init__(self):
        super().__init__('waypoint_search_node')
        self.declare_parameter('waypoints_file', '')
        self.declare_parameter('action_name', 'follow_waypoints')
        self.client = ActionClient(self, FollowWaypoints, str(self.get_parameter('action_name').value))
        self.sent = False
        self.timer = self.create_timer(1.0, self.tick)

    def load_waypoints(self) -> List[PoseStamped]:
        path = str(self.get_parameter('waypoints_file').value)
        if yaml is None:
            raise RuntimeError('PyYAML is required to load search_waypoints.yaml')
        with open(path, 'r', encoding='utf-8') as handle:
            data = yaml.safe_load(handle) or {}
        frame_id = data.get('frame_id', 'map')
        poses = []
        for item in data.get('waypoints', []):
            pose = PoseStamped()
            pose.header.frame_id = frame_id
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = float(item.get('x', 0.0))
            pose.pose.position.y = float(item.get('y', 0.0))
            pose.pose.orientation = quaternion_from_yaw(float(item.get('yaw', 0.0)))
            poses.append(pose)
        return poses

    def tick(self):
        if self.sent:
            return
        if not self.client.wait_for_server(timeout_sec=0.1):
            self.get_logger().info('Waiting for Nav2 follow_waypoints action server...')
            return
        try:
            poses = self.load_waypoints()
        except Exception as exc:
            self.get_logger().error(f'Could not load search waypoints: {exc}')
            self.sent = True
            return
        if not poses:
            self.get_logger().error('No waypoints configured for deterministic Billie search')
            self.sent = True
            return
        goal = FollowWaypoints.Goal()
        goal.poses = poses
        future = self.client.send_goal_async(goal, feedback_callback=self.feedback_callback)
        future.add_done_callback(self.goal_response_callback)
        self.sent = True
        self.get_logger().info(f'Sent deterministic search route with {len(poses)} waypoints')

    def feedback_callback(self, feedback_msg):
        self.get_logger().info(f'Current waypoint index: {feedback_msg.feedback.current_waypoint}')

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Search route goal rejected by Nav2')
            return
        self.get_logger().info('Search route goal accepted')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        result = future.result().result
        missed = list(result.missed_waypoints)
        if missed:
            self.get_logger().warn(f'Search route completed with missed waypoints: {missed}')
        else:
            self.get_logger().info('Search route completed successfully')


def main(args=None):
    rclpy.init(args=args)
    node = WaypointSearchNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

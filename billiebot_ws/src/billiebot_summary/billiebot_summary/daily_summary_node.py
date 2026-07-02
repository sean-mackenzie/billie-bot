#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from billiebot_summary.summary_generator import generate_summary


class DailySummaryNode(Node):
    def __init__(self):
        super().__init__('daily_summary_node')
        self.declare_parameter('database_path', '~/.billiebot/billiebot_events.sqlite3')
        self.declare_parameter('date', '')
        self.declare_parameter('output_path', '~/.billiebot/summaries')

    def run_once(self):
        summary, output_path = generate_summary(
            str(self.get_parameter('database_path').value),
            str(self.get_parameter('date').value),
            str(self.get_parameter('output_path').value),
        )
        self.get_logger().info(f'Daily summary written to {output_path}')
        self.get_logger().info(summary.replace('\n', ' | '))


def main(args=None):
    rclpy.init(args=args)
    node = DailySummaryNode()
    try:
        node.run_once()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

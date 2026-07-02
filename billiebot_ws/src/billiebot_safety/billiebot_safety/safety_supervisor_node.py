#!/usr/bin/env python3
import rclpy
from billiebot_msgs.msg import SystemMode
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Bool
from std_srvs.srv import SetBool


class SafetySupervisor(Node):
    def __init__(self) -> None:
        super().__init__('safety_supervisor_node')
        self.declare_parameter('input_cmd_topic', '/cmd_vel')
        self.declare_parameter('output_cmd_topic', '/cmd_vel_safe')
        self.declare_parameter('max_linear_velocity', 0.25)
        self.declare_parameter('max_angular_velocity', 0.9)
        self.declare_parameter('command_timeout_sec', 0.5)
        self.declare_parameter('stop_mode', False)
        self.declare_parameter('publish_rate_hz', 20.0)

        self.input_cmd_topic = str(self.get_parameter('input_cmd_topic').value)
        self.output_cmd_topic = str(self.get_parameter('output_cmd_topic').value)
        self.max_linear_velocity = float(self.get_parameter('max_linear_velocity').value)
        self.max_angular_velocity = float(self.get_parameter('max_angular_velocity').value)
        self.command_timeout_sec = float(self.get_parameter('command_timeout_sec').value)
        self.stop_mode = bool(self.get_parameter('stop_mode').value)

        self.latest_cmd = Twist()
        self.last_cmd_time = self.get_clock().now()
        self.estop_active = False
        self.estop_reason = ''

        self.create_subscription(Twist, self.input_cmd_topic, self.cmd_callback, 10)
        self.create_subscription(Bool, '/billiebot/estop', self.estop_topic_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, self.output_cmd_topic, 10)
        self.mode_pub = self.create_publisher(SystemMode, '/billiebot/mode', 10)
        self.create_service(SetBool, '/billiebot/set_estop', self.set_estop_callback)

        period = 1.0 / float(self.get_parameter('publish_rate_hz').value)
        self.timer = self.create_timer(period, self.tick)
        self.get_logger().info(f'Safety supervisor: {self.input_cmd_topic} -> {self.output_cmd_topic}')

    @staticmethod
    def clamp(value: float, limit: float) -> float:
        return max(-limit, min(limit, value))

    def cmd_callback(self, msg: Twist) -> None:
        safe = Twist()
        safe.linear.x = self.clamp(float(msg.linear.x), self.max_linear_velocity)
        safe.linear.y = 0.0
        safe.linear.z = 0.0
        safe.angular.x = 0.0
        safe.angular.y = 0.0
        safe.angular.z = self.clamp(float(msg.angular.z), self.max_angular_velocity)
        self.latest_cmd = safe
        self.last_cmd_time = self.get_clock().now()

    def estop_topic_callback(self, msg: Bool) -> None:
        self.estop_active = bool(msg.data)
        self.estop_reason = 'software_estop_topic' if self.estop_active else ''
        self.get_logger().warn(f'Software E-stop topic set to {self.estop_active}')

    def set_estop_callback(self, request: SetBool.Request, response: SetBool.Response):
        self.estop_active = bool(request.data)
        self.estop_reason = 'software_estop_service' if self.estop_active else ''
        response.success = True
        response.message = 'E-stop active' if self.estop_active else 'E-stop cleared'
        self.get_logger().warn(response.message)
        return response

    def publish_mode(self, mode: str, reason: str) -> None:
        msg = SystemMode()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.mode = mode
        msg.reason = reason
        self.mode_pub.publish(msg)

    def tick(self) -> None:
        now = self.get_clock().now()
        age = (now - self.last_cmd_time).nanoseconds * 1e-9
        output = Twist()
        if self.estop_active:
            self.publish_mode('estop', self.estop_reason)
        elif self.stop_mode:
            self.publish_mode('stopped', 'stop_mode_parameter')
        elif age > self.command_timeout_sec:
            self.publish_mode('idle', 'command_timeout')
        else:
            output = self.latest_cmd
            self.publish_mode('active', 'safe_command_forwarded')
        self.cmd_pub.publish(output)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SafetySupervisor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

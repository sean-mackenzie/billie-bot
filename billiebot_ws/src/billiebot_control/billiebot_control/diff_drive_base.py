#!/usr/bin/env python3
import math
import threading
from typing import Optional, Tuple

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster

try:
    import serial
except ImportError:  # pragma: no cover - exercised only on systems missing pyserial.
    serial = None


class DiffDriveBase(Node):
    """Serial bridge for the Arduino Nano motor controller.

    The serial protocol is adapted from reference_my_bot/diff-drive-motor-controller:
    `m L R` sets closed-loop counts-per-loop speeds, `e` reads encoder counts,
    and `r` resets encoder counters. Mock mode uses the same odometry model
    without opening a serial port.
    """

    def __init__(self) -> None:
        super().__init__('diff_drive_base')

        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 57600)
        self.declare_parameter('mock_hardware', False)
        self.declare_parameter('cmd_vel_topic', '/cmd_vel_safe')
        self.declare_parameter('wheel_radius', 0.034)
        self.declare_parameter('wheel_separation', 0.298)
        self.declare_parameter('encoder_ticks_per_rev', 2000.0)
        self.declare_parameter('pid_rate_hz', 30.0)
        self.declare_parameter('max_linear_velocity', 0.25)
        self.declare_parameter('max_angular_velocity', 0.9)
        self.declare_parameter('cmd_timeout_sec', 0.5)
        self.declare_parameter('publish_rate_hz', 30.0)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('left_joint_name', 'left_wheel_joint')
        self.declare_parameter('right_joint_name', 'right_wheel_joint')
        self.declare_parameter('left_motor_sign', 1.0)
        self.declare_parameter('right_motor_sign', 1.0)
        self.declare_parameter('left_encoder_sign', 1.0)
        self.declare_parameter('right_encoder_sign', 1.0)
        self.declare_parameter('reset_encoders_on_start', True)
        self.declare_parameter('publish_tf', True)

        self.port = str(self.get_parameter('port').value)
        self.baudrate = int(self.get_parameter('baudrate').value)
        self.mock_hardware = bool(self.get_parameter('mock_hardware').value)
        self.cmd_vel_topic = str(self.get_parameter('cmd_vel_topic').value)
        self.wheel_radius = float(self.get_parameter('wheel_radius').value)
        self.wheel_separation = float(self.get_parameter('wheel_separation').value)
        self.encoder_ticks_per_rev = float(self.get_parameter('encoder_ticks_per_rev').value)
        self.pid_rate_hz = float(self.get_parameter('pid_rate_hz').value)
        self.max_linear_velocity = float(self.get_parameter('max_linear_velocity').value)
        self.max_angular_velocity = float(self.get_parameter('max_angular_velocity').value)
        self.cmd_timeout_sec = float(self.get_parameter('cmd_timeout_sec').value)
        self.publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        self.odom_frame = str(self.get_parameter('odom_frame').value)
        self.base_frame = str(self.get_parameter('base_frame').value)
        self.left_joint_name = str(self.get_parameter('left_joint_name').value)
        self.right_joint_name = str(self.get_parameter('right_joint_name').value)
        self.left_motor_sign = float(self.get_parameter('left_motor_sign').value)
        self.right_motor_sign = float(self.get_parameter('right_motor_sign').value)
        self.left_encoder_sign = float(self.get_parameter('left_encoder_sign').value)
        self.right_encoder_sign = float(self.get_parameter('right_encoder_sign').value)
        self.reset_encoders_on_start = bool(self.get_parameter('reset_encoders_on_start').value)
        self.publish_tf_enabled = bool(self.get_parameter('publish_tf').value)

        self.cmd_sub = self.create_subscription(Twist, self.cmd_vel_topic, self.cmd_callback, 10)
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.serial_lock = threading.Lock()
        self.ser = None

        self.last_cmd_time = self.get_clock().now()
        self.target_linear = 0.0
        self.target_angular = 0.0
        self.target_left_rad_s = 0.0
        self.target_right_rad_s = 0.0

        self.prev_left_ticks_total: Optional[int] = None
        self.prev_right_ticks_total: Optional[int] = None
        self.left_pos = 0.0
        self.right_pos = 0.0
        self.left_vel = 0.0
        self.right_vel = 0.0
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.prev_time = self.get_clock().now()

        if self.mock_hardware:
            self.get_logger().warn('diff_drive_base running in mock_hardware mode; no serial port opened')
        else:
            self.connect_serial()
            if self.reset_encoders_on_start:
                self.reset_encoders()
            self.get_logger().info(
                f'Connected to Arduino bridge on {self.port} @ {self.baudrate} baud'
            )

        self.timer = self.create_timer(1.0 / self.publish_rate_hz, self.update)
        self.get_logger().info(f'Subscribed to velocity commands on {self.cmd_vel_topic}')

    def connect_serial(self) -> None:
        if serial is None:
            raise RuntimeError('python3-serial is required unless mock_hardware:=true')
        self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    @staticmethod
    def clamp(value: float, limit: float) -> float:
        return max(-limit, min(limit, value))

    def cmd_callback(self, msg: Twist) -> None:
        v = self.clamp(float(msg.linear.x), self.max_linear_velocity)
        w = self.clamp(float(msg.angular.z), self.max_angular_velocity)
        self.target_linear = v
        self.target_angular = w
        self.target_left_rad_s = (v - 0.5 * self.wheel_separation * w) / self.wheel_radius
        self.target_right_rad_s = (v + 0.5 * self.wheel_separation * w) / self.wheel_radius
        self.last_cmd_time = self.get_clock().now()

    def write_command(self, cmd: str) -> None:
        if self.ser is None:
            return
        with self.serial_lock:
            self.ser.write((cmd + '\r').encode('utf-8'))

    def read_line(self) -> Optional[str]:
        if self.ser is None:
            return None
        with self.serial_lock:
            raw = self.ser.readline()
        if not raw:
            return None
        return raw.decode('utf-8', errors='ignore').strip()

    def flush_input(self) -> None:
        if self.ser is not None:
            with self.serial_lock:
                self.ser.reset_input_buffer()

    def reset_encoders(self) -> None:
        self.flush_input()
        self.write_command('r')
        for _ in range(5):
            line = self.read_line()
            if line == 'OK':
                self.get_logger().info('Arduino encoder reset acknowledged')
                return
        self.get_logger().warn('Arduino encoder reset was not acknowledged')

    def rad_s_to_counts_per_loop(self, rad_s: float, sign: float) -> int:
        ticks_per_sec = (rad_s / (2.0 * math.pi)) * self.encoder_ticks_per_rev
        return int(round(sign * ticks_per_sec / self.pid_rate_hz))

    def send_motor_command(self, left_rad_s: float, right_rad_s: float) -> None:
        left_cpl = self.rad_s_to_counts_per_loop(left_rad_s, self.left_motor_sign)
        right_cpl = self.rad_s_to_counts_per_loop(right_rad_s, self.right_motor_sign)
        self.write_command(f'm {left_cpl} {right_cpl}')

    def read_encoders(self) -> Optional[Tuple[int, int]]:
        self.write_command('e')
        for _ in range(10):
            line = self.read_line()
            if not line or line == 'OK':
                continue
            parts = line.split()
            if len(parts) != 2:
                self.get_logger().warning(f'Unexpected encoder reply: "{line}"')
                continue
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                self.get_logger().warning(f'Unexpected encoder reply: "{line}"')
        return None

    def active_command(self) -> Tuple[float, float, float, float]:
        now = self.get_clock().now()
        if (now - self.last_cmd_time).nanoseconds * 1e-9 > self.cmd_timeout_sec:
            return 0.0, 0.0, 0.0, 0.0
        return (
            self.target_linear,
            self.target_angular,
            self.target_left_rad_s,
            self.target_right_rad_s,
        )

    def integrate_body_delta(self, dl: float, dr: float, dt: float) -> Tuple[float, float]:
        dc = 0.5 * (dl + dr)
        dyaw = (dr - dl) / self.wheel_separation
        if abs(dyaw) < 1e-12:
            self.x += dc * math.cos(self.yaw)
            self.y += dc * math.sin(self.yaw)
        else:
            self.x += dc * math.cos(self.yaw + 0.5 * dyaw)
            self.y += dc * math.sin(self.yaw + 0.5 * dyaw)
        self.yaw += dyaw
        return dc / dt, dyaw / dt

    def update_mock(self, dt: float) -> Tuple[float, float]:
        v, w, left_cmd, right_cmd = self.active_command()
        dleft_rad = left_cmd * dt
        dright_rad = right_cmd * dt
        self.left_pos += dleft_rad
        self.right_pos += dright_rad
        self.left_vel = left_cmd
        self.right_vel = right_cmd
        self.x += v * math.cos(self.yaw) * dt
        self.y += v * math.sin(self.yaw) * dt
        self.yaw += w * dt
        return v, w

    def update_serial(self, dt: float) -> Optional[Tuple[float, float]]:
        _, _, left_cmd, right_cmd = self.active_command()
        self.send_motor_command(left_cmd, right_cmd)
        enc = self.read_encoders()
        if enc is None:
            self.get_logger().warning('No encoder response from motor controller')
            return None

        raw_left_ticks, raw_right_ticks = enc
        left_ticks = int(round(self.left_encoder_sign * raw_left_ticks))
        right_ticks = int(round(self.right_encoder_sign * raw_right_ticks))

        if self.prev_left_ticks_total is None or self.prev_right_ticks_total is None:
            self.prev_left_ticks_total = left_ticks
            self.prev_right_ticks_total = right_ticks
            return 0.0, 0.0

        dleft_ticks = left_ticks - self.prev_left_ticks_total
        dright_ticks = right_ticks - self.prev_right_ticks_total
        self.prev_left_ticks_total = left_ticks
        self.prev_right_ticks_total = right_ticks

        rad_per_tick = (2.0 * math.pi) / self.encoder_ticks_per_rev
        dleft_rad = dleft_ticks * rad_per_tick
        dright_rad = dright_ticks * rad_per_tick
        self.left_pos += dleft_rad
        self.right_pos += dright_rad
        self.left_vel = dleft_rad / dt
        self.right_vel = dright_rad / dt
        return self.integrate_body_delta(dleft_rad * self.wheel_radius, dright_rad * self.wheel_radius, dt)

    def publish_joint_states(self, stamp) -> None:
        msg = JointState()
        msg.header.stamp = stamp
        msg.name = [self.left_joint_name, self.right_joint_name]
        msg.position = [self.left_pos, self.right_pos]
        msg.velocity = [self.left_vel, self.right_vel]
        self.joint_pub.publish(msg)

    def publish_odom(self, stamp, vx: float, wz: float) -> None:
        msg = Odometry()
        msg.header.stamp = stamp
        msg.header.frame_id = self.odom_frame
        msg.child_frame_id = self.base_frame
        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(self.yaw / 2.0)
        msg.twist.twist.linear.x = vx
        msg.twist.twist.angular.z = wz
        self.odom_pub.publish(msg)

    def publish_tf(self, stamp) -> None:
        if not self.publish_tf_enabled:
            return
        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = self.odom_frame
        transform.child_frame_id = self.base_frame
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.rotation.z = math.sin(self.yaw / 2.0)
        transform.transform.rotation.w = math.cos(self.yaw / 2.0)
        self.tf_broadcaster.sendTransform(transform)

    def update(self) -> None:
        now = self.get_clock().now()
        dt = (now - self.prev_time).nanoseconds * 1e-9
        if dt <= 0.0:
            return

        result = self.update_mock(dt) if self.mock_hardware else self.update_serial(dt)
        if result is None:
            return

        vx, wz = result
        stamp = now.to_msg()
        self.publish_joint_states(stamp)
        self.publish_odom(stamp, vx, wz)
        self.publish_tf(stamp)
        self.prev_time = now

    def stop_robot(self) -> None:
        self.target_linear = 0.0
        self.target_angular = 0.0
        self.target_left_rad_s = 0.0
        self.target_right_rad_s = 0.0
        try:
            self.write_command('m 0 0')
        except Exception:
            pass

    def destroy_node(self):
        self.stop_robot()
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
        super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DiffDriveBase()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import json
import os
import sqlite3
from typing import Optional

import rclpy
from billiebot_msgs.msg import (
    AudioEvent,
    BillieDetectionArray,
    BillieStateObservation,
    EventLogStatus,
)
from rclpy.node import Node
from std_msgs.msg import String


def stamp_to_float(stamp) -> float:
    return float(stamp.sec) + float(stamp.nanosec) * 1e-9


class EventLoggerNode(Node):
    def __init__(self):
        super().__init__('event_logger_node')
        self.declare_parameter('database_path', '~/.billiebot/billiebot_events.sqlite3')
        self.declare_parameter('save_media_references', True)
        self.declare_parameter('log_detections', True)
        self.declare_parameter('log_audio_events', True)
        self.declare_parameter('log_state_observations', True)

        self.database_path = os.path.expanduser(str(self.get_parameter('database_path').value))
        database_dir = os.path.dirname(self.database_path)
        if database_dir:
            os.makedirs(database_dir, exist_ok=True)
        self.conn = sqlite3.connect(self.database_path)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.init_db()

        self.status_pub = self.create_publisher(EventLogStatus, '/billie/events_logged', 10)
        self.create_subscription(BillieStateObservation, '/billie/state', self.state_callback, 50)
        self.create_subscription(BillieDetectionArray, '/billie/detections', self.detections_callback, 50)
        self.create_subscription(AudioEvent, '/billie/audio_events', self.audio_callback, 50)
        self.create_subscription(String, '/billiebot/health', self.health_callback, 10)
        self.get_logger().info(f'Logging BillieBot events to {self.database_path}')

    def init_db(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              stamp REAL NOT NULL,
              event_type TEXT NOT NULL,
              state_label TEXT,
              confidence REAL,
              evidence_source TEXT,
              robot_x REAL,
              robot_y REAL,
              billie_x REAL,
              billie_y REAL,
              media_reference TEXT,
              raw_json TEXT
            );

            CREATE TABLE IF NOT EXISTS detections (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              stamp REAL NOT NULL,
              detector_name TEXT,
              class_label TEXT,
              confidence REAL,
              bbox_x REAL,
              bbox_y REAL,
              bbox_width REAL,
              bbox_height REAL,
              range_m REAL,
              bearing_rad REAL,
              is_billie_candidate INTEGER,
              raw_json TEXT
            );

            CREATE TABLE IF NOT EXISTS audio_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              stamp REAL NOT NULL,
              event_type TEXT NOT NULL,
              confidence REAL,
              loudness_db REAL,
              duration_s REAL,
              doa_rad REAL,
              raw_json TEXT
            );

            CREATE TABLE IF NOT EXISTS daily_summaries (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              summary_date TEXT NOT NULL UNIQUE,
              generated_at REAL NOT NULL,
              output_path TEXT,
              summary_text TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def publish_status(self, success: bool, message: str):
        msg = EventLogStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.success = bool(success)
        msg.database_path = self.database_path
        msg.message = message
        self.status_pub.publish(msg)

    def execute(self, sql: str, values: tuple, status_message: str):
        try:
            self.conn.execute(sql, values)
            self.conn.commit()
            self.publish_status(True, status_message)
        except sqlite3.Error as exc:
            self.get_logger().error(f'SQLite write failed: {exc}')
            self.publish_status(False, str(exc))

    def state_callback(self, msg: BillieStateObservation):
        if not bool(self.get_parameter('log_state_observations').value):
            return
        media_reference: Optional[str] = msg.media_reference
        if not bool(self.get_parameter('save_media_references').value):
            media_reference = ''
        raw = {
            'state_label': msg.state_label,
            'confidence': msg.confidence,
            'evidence_source': msg.evidence_source,
            'media_reference': media_reference,
        }
        self.execute(
            """
            INSERT INTO events (
              stamp, event_type, state_label, confidence, evidence_source,
              robot_x, robot_y, billie_x, billie_y, media_reference, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stamp_to_float(msg.header.stamp),
                'state_observation',
                msg.state_label,
                msg.confidence,
                msg.evidence_source,
                msg.robot_pose.pose.position.x,
                msg.robot_pose.pose.position.y,
                msg.estimated_billie_pose.pose.position.x,
                msg.estimated_billie_pose.pose.position.y,
                media_reference,
                json.dumps(raw),
            ),
            f'logged state_observation {msg.state_label}',
        )

    def detections_callback(self, msg: BillieDetectionArray):
        if not bool(self.get_parameter('log_detections').value):
            return
        for det in msg.detections:
            raw = {
                'detector_name': det.detector_name,
                'class_label': det.class_label,
                'confidence': det.confidence,
                'range_m': det.range_m,
                'bearing_rad': det.bearing_rad,
                'is_billie_candidate': det.is_billie_candidate,
            }
            self.execute(
                """
                INSERT INTO detections (
                  stamp, detector_name, class_label, confidence, bbox_x, bbox_y,
                  bbox_width, bbox_height, range_m, bearing_rad, is_billie_candidate, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stamp_to_float(det.header.stamp),
                    det.detector_name,
                    det.class_label,
                    det.confidence,
                    det.bbox_x,
                    det.bbox_y,
                    det.bbox_width,
                    det.bbox_height,
                    det.range_m,
                    det.bearing_rad,
                    int(det.is_billie_candidate),
                    json.dumps(raw),
                ),
                'logged detection',
            )

    def audio_callback(self, msg: AudioEvent):
        if not bool(self.get_parameter('log_audio_events').value):
            return
        raw = {
            'event_type': msg.event_type,
            'confidence': msg.confidence,
            'loudness_db': msg.loudness_db,
            'duration_s': msg.duration_s,
            'doa_rad': msg.doa_rad,
        }
        self.execute(
            """
            INSERT INTO audio_events (
              stamp, event_type, confidence, loudness_db, duration_s, doa_rad, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stamp_to_float(msg.header.stamp),
                msg.event_type,
                msg.confidence,
                msg.loudness_db,
                msg.duration_s,
                msg.doa_rad,
                json.dumps(raw),
            ),
            f'logged audio_event {msg.event_type}',
        )

    def health_callback(self, msg: String):
        raw = {'message': msg.data}
        self.execute(
            """
            INSERT INTO events (
              stamp, event_type, state_label, confidence, evidence_source,
              robot_x, robot_y, billie_x, billie_y, media_reference, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stamp_to_float(self.get_clock().now().to_msg()),
                'health',
                msg.data,
                1.0,
                'health_topic',
                None,
                None,
                None,
                None,
                '',
                json.dumps(raw),
            ),
            'logged health event',
        )

    def destroy_node(self):
        try:
            self.conn.close()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = EventLoggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

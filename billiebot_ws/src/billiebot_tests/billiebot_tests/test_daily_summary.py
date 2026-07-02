#!/usr/bin/env python3
"""
Test Objective:
  Seed a test database, run the summary generator, and verify text/database output.
Required Hardware:
  None.
Setup:
  No ROS graph is required.
Launch:
  ros2 run billiebot_tests test_daily_summary
Verification:
  The script creates a temporary SQLite database and summary markdown file.
Pass Criteria:
  Summary text includes expected counts and daily_summaries has a row.
Fail Criteria:
  Summary file is missing or database row is absent.
Notes:
  This is a deterministic no-cloud unit-style verification.
"""
import datetime as dt
import os
import sqlite3
import tempfile

from billiebot_summary.summary_generator import generate_summary


def fail(message: str):
    raise SystemExit(f'FAIL: {message}')


def pass_msg(message: str):
    print(f'PASS: {message}')


def main():
    day = dt.datetime.now().date()
    stamp = dt.datetime.combine(day, dt.time(hour=12)).timestamp()
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'events.sqlite3')
        out_dir = os.path.join(tmpdir, 'summaries')
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            CREATE TABLE detections (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              stamp REAL, detector_name TEXT, class_label TEXT, confidence REAL,
              bbox_x REAL, bbox_y REAL, bbox_width REAL, bbox_height REAL,
              range_m REAL, bearing_rad REAL, is_billie_candidate INTEGER, raw_json TEXT
            );
            CREATE TABLE audio_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              stamp REAL, event_type TEXT, confidence REAL, loudness_db REAL,
              duration_s REAL, doa_rad REAL, raw_json TEXT
            );
            CREATE TABLE events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              stamp REAL, event_type TEXT, state_label TEXT, confidence REAL,
              evidence_source TEXT, robot_x REAL, robot_y REAL, billie_x REAL,
              billie_y REAL, media_reference TEXT, raw_json TEXT
            );
            """
        )
        conn.execute("INSERT INTO detections (stamp, is_billie_candidate) VALUES (?, 1)", (stamp,))
        conn.execute("INSERT INTO audio_events (stamp, event_type) VALUES (?, 'bark')", (stamp,))
        conn.execute("INSERT INTO audio_events (stamp, event_type) VALUES (?, 'loud_noise')", (stamp,))
        conn.execute("INSERT INTO events (stamp, event_type, state_label, robot_x, robot_y) VALUES (?, 'state_observation', 'sleeping', 1.0, 2.0)", (stamp,))
        conn.commit()
        conn.close()
        summary, output_path = generate_summary(db_path, day.isoformat(), out_dir)
        if not os.path.exists(output_path):
            fail('Summary file was not created')
        if 'Total visual detections: 1' not in summary or 'Likely bark count: 1' not in summary:
            fail('Summary text did not include expected seeded counts')
        conn = sqlite3.connect(db_path)
        row = conn.execute('SELECT COUNT(*) FROM daily_summaries').fetchone()
        conn.close()
        if int(row[0]) != 1:
            fail('daily_summaries row was not written')
        pass_msg(f'daily summary generated at {output_path}')


if __name__ == '__main__':
    main()

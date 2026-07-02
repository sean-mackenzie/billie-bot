#!/usr/bin/env python3
import datetime as dt
import os
import sqlite3
import time
from typing import Optional, Tuple


def resolve_date(date_text: str) -> dt.date:
    if date_text:
        return dt.date.fromisoformat(date_text)
    return dt.datetime.now().date()


def day_bounds(day: dt.date) -> Tuple[float, float]:
    start = dt.datetime.combine(day, dt.time.min)
    end = start + dt.timedelta(days=1)
    return start.timestamp(), end.timestamp()


def ensure_summary_table(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_summaries (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          summary_date TEXT NOT NULL UNIQUE,
          generated_at REAL NOT NULL,
          output_path TEXT,
          summary_text TEXT NOT NULL
        )
        """
    )
    conn.commit()


def scalar(conn: sqlite3.Connection, sql: str, values: tuple = ()) -> int:
    row = conn.execute(sql, values).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def generate_summary(database_path: str, date_text: str = '', output_path: Optional[str] = None) -> Tuple[str, str]:
    database_path = os.path.expanduser(database_path)
    day = resolve_date(date_text)
    start, end = day_bounds(day)
    output_path = os.path.expanduser(output_path or os.path.join('~/.billiebot/summaries'))

    conn = sqlite3.connect(database_path)
    ensure_summary_table(conn)

    detections = scalar(
        conn,
        'SELECT COUNT(*) FROM detections WHERE stamp >= ? AND stamp < ? AND is_billie_candidate = 1',
        (start, end),
    )
    barks = scalar(
        conn,
        "SELECT COUNT(*) FROM audio_events WHERE stamp >= ? AND stamp < ? AND event_type = 'bark'",
        (start, end),
    )
    loud_noises = scalar(
        conn,
        "SELECT COUNT(*) FROM audio_events WHERE stamp >= ? AND stamp < ? AND event_type = 'loud_noise'",
        (start, end),
    )
    sleeping = scalar(
        conn,
        "SELECT COUNT(*) FROM events WHERE stamp >= ? AND stamp < ? AND state_label IN ('sleeping', 'resting')",
        (start, end),
    )
    nav_issues = scalar(
        conn,
        """
        SELECT COUNT(*) FROM events
        WHERE stamp >= ? AND stamp < ?
          AND (event_type IN ('health', 'navigation', 'safety')
               OR lower(coalesce(state_label, '')) LIKE '%stuck%'
               OR lower(coalesce(state_label, '')) LIKE '%recovery%'
               OR lower(coalesce(state_label, '')) LIKE '%estop%')
        """,
        (start, end),
    )

    location_rows = conn.execute(
        """
        SELECT ROUND(robot_x, 1) AS rx, ROUND(robot_y, 1) AS ry, COUNT(*) AS c
        FROM events
        WHERE stamp >= ? AND stamp < ? AND robot_x IS NOT NULL AND robot_y IS NOT NULL
        GROUP BY rx, ry
        ORDER BY c DESC
        LIMIT 3
        """,
        (start, end),
    ).fetchall()

    if location_rows:
        locations = ', '.join([f'({row[0]:.1f}, {row[1]:.1f}) x{row[2]}' for row in location_rows])
    else:
        locations = 'No reliable robot-location observations recorded.'

    summary = "\n".join([
        f'# Billie Daily Summary - {day.isoformat()}',
        '',
        f'- Total visual detections: {detections}',
        f'- Likely bark count: {barks}',
        f'- Loud noise count: {loud_noises}',
        f'- Sleeping/resting observations: {sleeping}',
        f'- Most common observed robot locations: {locations}',
        f'- Navigation/safety issues logged: {nav_issues}',
        '',
        'This summary is deterministic and generated only from local SQLite events.',
    ])

    if os.path.isdir(output_path) or not os.path.splitext(output_path)[1]:
        os.makedirs(output_path, exist_ok=True)
        final_output = os.path.join(output_path, f'billie_summary_{day.isoformat()}.md')
    else:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        final_output = output_path

    with open(final_output, 'w', encoding='utf-8') as handle:
        handle.write(summary + '\n')

    conn.execute(
        """
        INSERT INTO daily_summaries (summary_date, generated_at, output_path, summary_text)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(summary_date) DO UPDATE SET
          generated_at = excluded.generated_at,
          output_path = excluded.output_path,
          summary_text = excluded.summary_text
        """,
        (day.isoformat(), time.time(), final_output, summary),
    )
    conn.commit()
    conn.close()
    return summary, final_output

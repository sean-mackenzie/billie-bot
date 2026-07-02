#!/usr/bin/env bash
set -euo pipefail

if ! command -v ros2 >/dev/null 2>&1; then
  echo "ros2 is not available. Source ROS 2 Humble and the BillieBot workspace first." >&2
  exit 1
fi

echo "[1/7] deterministic daily summary"
ros2 run billiebot_tests test_daily_summary

DB_PATH="$(mktemp -t billiebot_smoke_XXXXXX.sqlite3)"
LOG_PATH="$(mktemp -t billiebot_smoke_XXXXXX.log)"

echo "[2/7] launching mock MVP stack"
ros2 launch billiebot_bringup mvp_full.launch.py \
  mock_hardware:=true \
  mock_lidar:=true \
  mock_camera:=true \
  detector_backend:=mock \
  mock_publish_detection:=true \
  mock_audio_events:=true \
  database_path:="${DB_PATH}" >"${LOG_PATH}" 2>&1 &
LAUNCH_PID=$!
trap 'kill ${LAUNCH_PID} >/dev/null 2>&1 || true' EXIT
sleep 10

echo "[3/7] mock lidar"
ros2 run billiebot_tests test_lidar_scan --ros-args -p timeout_sec:=5.0 -p min_hz:=1.0

echo "[4/7] mock camera"
ros2 run billiebot_tests test_camera_oakd --ros-args -p timeout_sec:=5.0

echo "[5/7] mock visual detection"
ros2 run billiebot_tests test_billie_visual_detection --ros-args -p require_detection:=true

echo "[6/7] mock bark/audio event"
ros2 run billiebot_tests test_bark_detection

echo "[7/7] state logging"
ros2 run billiebot_tests test_state_logging --ros-args -p database_path:="${DB_PATH}"

echo "Smoke tests passed. Mock stack log: ${LOG_PATH}"

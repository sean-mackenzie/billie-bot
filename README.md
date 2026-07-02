# BillieBot

BillieBot is a ROS 2 Humble MVP for an apartment-scale AI dog companion / dog behavior robot built for Billie, a miniature dachshund.

The MVP supports:

- Conservative autonomous apartment navigation.
- Deterministic waypoint search for Billie.
- RGB/depth visual detection plumbing for Billie observations.
- Bark and loud-event detection.
- Rule-based Billie state observations.
- Structured SQLite event logging.
- Deterministic daily activity summaries.

The MVP intentionally does not implement Behavior AI, reinforcement learning, contextual bandits, treat dispensing, autonomous speech engagement, or social interaction policies. The package boundaries, messages, and logging schema are prepared so those systems can be added later without putting policy logic inside safety, control, or navigation.

## Repository Layout

The ROS 2 workspace is in [`billiebot_ws`](billiebot_ws):

```text
billiebot_ws/src
├── billiebot_audio
├── billiebot_bringup
├── billiebot_control
├── billiebot_description
├── billiebot_logging
├── billiebot_msgs
├── billiebot_navigation
├── billiebot_perception
├── billiebot_safety
├── billiebot_state
├── billiebot_summary
└── billiebot_tests
```

Detailed architecture, launch, calibration, and verification notes are in [`billiebot_ws/README.md`](billiebot_ws/README.md).

## Target Hardware

- Jetson Orin Nano running Ubuntu 22.04 and ROS 2 Humble.
- Differential-drive base with two DC encoder motors, 68 mm wheels, caster wheel, and 3S LiPo power.
- RPLidar A1 lidar.
- OAK-D Lite RGB/depth camera.
- ReSpeaker XVF3800 microphone array.
- DFRobot BNO055/BMP280 IMU.
- Arduino Nano motor controller using the included serial bridge firmware.

Mock lidar, camera, audio, and drive modes are included so the core ROS graph can run without all hardware attached.

## Build

On the Ubuntu 22.04 / ROS 2 Humble target:

```bash
cd billiebot_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

## Run

Start the full MVP stack in mock/no-hardware mode:

```bash
ros2 launch billiebot_bringup mvp_full.launch.py \
  mock_hardware:=true \
  mock_lidar:=true \
  mock_camera:=true \
  detector_backend:=mock \
  mock_publish_detection:=true \
  mock_audio_events:=true
```

Incremental bring-up examples:

```bash
ros2 launch billiebot_bringup description.launch.py
ros2 launch billiebot_bringup lidar.launch.py mock_lidar:=false
ros2 launch billiebot_bringup drive.launch.py mock_hardware:=false
ros2 launch billiebot_bringup slam.launch.py mock_lidar:=false mock_hardware:=false
ros2 launch billiebot_bringup vision.launch.py mock_camera:=false detector_backend:=mock
ros2 launch billiebot_bringup audio.launch.py
ros2 launch billiebot_bringup state.launch.py
ros2 launch billiebot_bringup logging.launch.py
```

## Test

Run the mock smoke sequence after building and sourcing the workspace:

```bash
ros2 run billiebot_tests run_mvp_smoke_tests.sh
```

Individual verification scripts live in `billiebot_tests` and cover motor spin, encoders, lidar, OAK-D topics, audio events, teleop drive, 1 m forward calibration, 360 degree rotation calibration, SLAM, AMCL, Nav2 goals, deterministic search routes, visual detections, bark detection, state logging, daily summaries, and safety stop behavior.

Manual procedures are included for power rail validation and stuck recovery testing.

## Hardware Configuration Notes

Update these values before hardware bring-up:

- Motor controller serial path in `billiebot_control/config/base_driver.yaml`.
- RPLidar serial path in `billiebot_navigation/launch/lidar.launch.py` or launch arguments.
- OAK-D driver topic names if the installed DepthAI ROS driver differs from the defaults.
- ReSpeaker/XVF3800 audio device name if using direct local capture.
- Wheel radius, wheel separation, encoder ticks, and motor/encoder signs after calibration.

## Future Integration Points

Future Behavior AI should consume `/billie/state`, `/billie/detections`, `/billie/audio_events`, `/billiebot/mode`, and the SQLite event log. It should publish normal navigation commands through `/cmd_vel` so `billiebot_safety` remains the final gate before `/cmd_vel_safe`.

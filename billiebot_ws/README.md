# BillieBot MVP ROS 2 Workspace

## BillieBot MVP Overview

BillieBot is an AI dog companion / dog behavior robot MVP for a miniature dachshund named Billie. This workspace targets ROS 2 Humble on Ubuntu 22.04 and a Jetson Orin Nano. The MVP supports conservative apartment navigation, deterministic Billie search, visual Billie detection plumbing, bark/loud-event detection, rule-based state observations, SQLite event logging, and deterministic daily summaries.

The MVP intentionally does not implement Behavior AI, reinforcement learning, contextual bandits, treat dispensing, autonomous speech engagement, or social interaction policies. Interfaces and logs are structured so those systems can be added later as separate packages.

## Hardware Assumptions

- Differential-drive base with 68 mm wheels, approximately 0.298 m track width, and caster support.
- RPLidar A1 publishes `/scan` in `laser_frame`.
- OAK-D Lite publishes RGB/depth topics. The launch files default to mock camera mode because DepthAI driver setup is system-specific.
- ReSpeaker XVF3800 microphone array is represented by `mic_link`; direct Linux audio capture is optional and system-specific.
- DFRobot BNO055/BMP280 IMU is represented in the URDF as `imu_link`; no MVP IMU fusion node is implemented yet.
- Arduino Nano motor firmware uses the reference serial protocol: `m L R`, `e`, and `r` with carriage return at 57600 baud.
- Default hardware device paths are examples and must be updated for the Jetson:
  `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` for motor control and an RPLidar USB serial path for lidar.

## ROS 2 Package Map

- `billiebot_msgs`: custom detection, audio, state, logging, and mode messages.
- `billiebot_description`: BillieBot URDF/xacro, TF frames, robot_state_publisher launch, RViz config.
- `billiebot_control`: Arduino serial motor bridge, odometry, joint states, TF, calibration helpers, copied firmware reference.
- `billiebot_safety`: `/cmd_vel` clamp/timeout/E-stop supervisor publishing `/cmd_vel_safe`.
- `billiebot_navigation`: RPLidar/mock lidar, SLAM Toolbox, AMCL, Nav2 configs, deterministic waypoint search.
- `billiebot_perception`: OAK-D/mock camera launch, Billie detector placeholder, visual state helper.
- `billiebot_audio`: threshold/mock audio event detector.
- `billiebot_state`: rule-based fusion into `/billie/state`.
- `billiebot_logging`: SQLite event logger.
- `billiebot_summary`: deterministic daily summary CLI/node.
- `billiebot_bringup`: integrated launch sequence.
- `billiebot_tests`: discrete verification scripts and manual procedures.

## Build Instructions

Install ROS 2 Humble and package dependencies such as Nav2, SLAM Toolbox, RPLidar, DepthAI ROS driver if using OAK-D hardware, and `python3-serial`.

```bash
cd billiebot_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

## Incremental Bring-Up Sequence

1. Launch robot description

   ```bash
   ros2 launch billiebot_bringup description.launch.py
   ```

   Verify:

   ```bash
   ros2 topic echo /tf
   ros2 run tf2_tools view_frames
   ```

2. Launch lidar

   ```bash
   ros2 launch billiebot_bringup lidar.launch.py mock_lidar:=false
   ```

   Verify:

   ```bash
   ros2 topic hz /scan
   ros2 topic echo /scan --once
   ```

3. Launch drive

   ```bash
   ros2 launch billiebot_bringup drive.launch.py mock_hardware:=false
   ```

   Verify:

   ```bash
   ros2 topic echo /odom
   ros2 topic echo /tf
   ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.05}, angular: {z: 0.0}}" -r 5
   ```

4. Launch SLAM

   ```bash
   ros2 launch billiebot_bringup slam.launch.py mock_lidar:=false mock_hardware:=false
   ```

   Verify:

   ```bash
   ros2 topic echo /map --once
   ```

5. Launch AMCL/localization

   ```bash
   ros2 launch billiebot_bringup amcl.launch.py map:=/path/to/map.yaml
   ```

   Verify:

   ```bash
   ros2 topic echo /amcl_pose
   ros2 run tf2_ros tf2_echo map odom
   ```

6. Launch Nav2

   ```bash
   ros2 launch billiebot_bringup nav2.launch.py map:=/path/to/map.yaml
   ```

   Verify:

   ```bash
   ros2 lifecycle nodes
   ros2 action list
   ```

   Send a goal in RViz.

7. Launch OAK-D

   ```bash
   ros2 launch billiebot_bringup oakd.launch.py mock_camera:=false
   ```

   Verify:

   ```bash
   ros2 topic list | grep image
   ros2 topic hz /oak/rgb/image_raw
   ros2 topic hz /oak/stereo/depth
   ```

8. Launch vision

   ```bash
   ros2 launch billiebot_bringup vision.launch.py mock_camera:=false detector_backend:=mock
   ```

   Verify:

   ```bash
   ros2 topic echo /billie/detections
   ```

9. Launch audio

   ```bash
   ros2 launch billiebot_bringup audio.launch.py
   ```

   Verify:

   ```bash
   ros2 topic echo /billie/audio_events
   ```

10. Launch state estimator

   ```bash
   ros2 launch billiebot_bringup state.launch.py
   ```

   Verify:

   ```bash
   ros2 topic echo /billie/state
   ```

11. Launch logging

   ```bash
   ros2 launch billiebot_bringup logging.launch.py
   ```

   Verify:

   ```bash
   ros2 topic echo /billie/events_logged
   ls ~/.billiebot/billiebot_events.sqlite3
   ```

12. Launch full MVP

   ```bash
   ros2 launch billiebot_bringup mvp_full.launch.py
   ```

## Launch Files and Expected Topics

- `description.launch.py`: `/tf`, `/robot_description` parameter.
- `lidar.launch.py`: `/scan`.
- `drive.launch.py`: `/cmd_vel`, `/cmd_vel_safe`, `/odom`, `/joint_states`, `/tf`.
- `slam.launch.py`: `/scan`, `/odom`, `/map`.
- `amcl.launch.py`: `/amcl_pose`, `map -> odom`.
- `nav2.launch.py`: Nav2 lifecycle nodes, action servers, `/cmd_vel`.
- `oakd.launch.py`: `/oak/rgb/image_raw`, `/oak/stereo/depth`, `/oak/rgb/camera_info`.
- `vision.launch.py`: `/billie/detections`, optional `/billie/detections/debug_image`.
- `audio.launch.py`: `/billie/audio_events`.
- `state.launch.py`: `/billie/state`.
- `logging.launch.py`: `/billie/events_logged`, SQLite database.
- `summary.launch.py`: summary markdown and `daily_summaries` row.
- `mvp_full.launch.py`: full MVP stack in mock mode by default.

## Verification Test Plan

Run individual tests after launching the relevant subsystem:

```bash
ros2 run billiebot_tests test_motor_spin
ros2 run billiebot_tests test_encoder_counts
ros2 run billiebot_tests test_lidar_scan
ros2 run billiebot_tests test_camera_oakd
ros2 run billiebot_tests test_audio_event --ros-args -p mock_inject:=true
ros2 run billiebot_tests test_teleop_drive
ros2 run billiebot_tests test_forward_1m
ros2 run billiebot_tests test_rotate_360
ros2 run billiebot_tests test_slam_map
ros2 run billiebot_tests test_localization_amcl
ros2 run billiebot_tests test_nav2_waypoint
ros2 run billiebot_tests test_search_route --ros-args -p waypoints_file:=/path/to/search_waypoints.yaml
ros2 run billiebot_tests test_billie_visual_detection --ros-args -p require_detection:=true
ros2 run billiebot_tests test_bark_detection --ros-args -p mock_inject:=true
ros2 run billiebot_tests test_state_logging --ros-args -p database_path:=/tmp/billiebot_test.sqlite3
ros2 run billiebot_tests test_daily_summary
ros2 run billiebot_tests test_safety_stop
```

Manual procedures are installed in `billiebot_tests/manual`:

- `test_power_rail_manual.md`
- `test_stuck_recovery_manual.md`

## Mock Mode / No-Hardware Testing

Most launch files default to mock mode so package wiring can be tested without hardware:

```bash
ros2 launch billiebot_bringup mvp_full.launch.py \
  mock_hardware:=true \
  mock_lidar:=true \
  mock_camera:=true \
  detector_backend:=mock \
  mock_publish_detection:=true \
  mock_audio_events:=true
```

Run the smoke test sequence:

```bash
ros2 run billiebot_tests run_mvp_smoke_tests.sh
```

## Calibration Procedure

1. Confirm motor signs with the robot on blocks:

   ```bash
   ros2 run billiebot_tests test_motor_spin --ros-args -p verify_odom:=true
   ```

2. Tune forward distance:

   ```bash
   ros2 run billiebot_control command_forward_1m
   ros2 run billiebot_tests test_forward_1m
   ```

   Adjust `wheel_radius` or `encoder_ticks_per_rev` in `billiebot_control/config/base_driver.yaml`.

3. Tune rotation:

   ```bash
   ros2 run billiebot_control command_rotate_360
   ros2 run billiebot_tests test_rotate_360
   ```

   Adjust `wheel_separation` and motor/encoder sign parameters.

## Known Limitations

- OAK-D hardware launch assumes `depthai_ros_driver` is installed and may need topic remaps for the local driver version.
- ReSpeaker direct capture uses optional `sounddevice`; threshold topic/mock mode is the most portable MVP path.
- IMU and battery telemetry frames are modeled, but no MVP sensor fusion or voltage monitoring node is included.
- The visual detector is a placeholder unless an OpenCV/Ultralytics model is configured later.
- `mvp_full.launch.py` starts Nav2 wiring, but map-based navigation still requires a valid map and localized robot.
- Search behavior is deterministic waypoint following only.

## Future Behavior AI Integration Points

- Consume `/billie/state`, `/billie/detections`, `/billie/audio_events`, `/billiebot/mode`, and SQLite event history.
- Add future packages downstream of `billiebot_state` and `billiebot_logging` rather than modifying motor control or safety.
- Extend `daily_summaries` with richer local analytics before adding optional LLM/cloud summarization.
- Add new action/policy packages behind `/cmd_vel` so `billiebot_safety` remains the final gate before `/cmd_vel_safe`.

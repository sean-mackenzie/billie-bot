# test_stuck_recovery_manual

Test Objective:
Verify Nav2 recovery behavior when the robot path is blocked.

Required Hardware:
BillieBot drive base, lidar, map/localization or SLAM, a soft obstacle.

Setup:
Use a clear area. Launch navigation with conservative velocity limits. Place a soft obstacle in the planned path after the goal is accepted.

Launch:
`ros2 launch billiebot_bringup mvp_full.launch.py mock_hardware:=false mock_lidar:=false mock_camera:=true`

Verification:
Send a reachable Nav2 goal in RViz, block the path, and observe recovery behavior, `/cmd_vel`, and Nav2 logs.

Pass Criteria:
Robot slows/stops safely, recovery behavior executes, and Nav2 either replans or reports a useful failure without sustained wheel pushing.

Fail Criteria:
Robot keeps pushing into the obstacle, exceeds conservative speeds, fails to stop, or recovery behavior cannot be observed/reported.

Notes:
This is deterministic Nav2 recovery validation, not Behavior AI.

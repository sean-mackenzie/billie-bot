# test_power_rail_manual

Test Objective:
Verify 5 V rail stability under realistic load.

Required Hardware:
BillieBot power system, multimeter or oscilloscope, Jetson Orin Nano, motor controller, lidar, OAK-D, microphone array.

Setup:
Place the robot on blocks. Connect measurement probes to the regulated 5 V rail at the load side. Launch mock software first, then hardware subsystems one at a time.

Launch:
`ros2 launch billiebot_bringup drive.launch.py mock_hardware:=false`
`ros2 launch billiebot_bringup lidar.launch.py mock_lidar:=false`
`ros2 launch billiebot_bringup oakd.launch.py mock_camera:=false`

Verification:
Measure voltage at idle, during lidar spin-up, during camera streaming, and while commanding low motor speed.

Pass Criteria:
5 V rail remains within the regulator and Jetson/device tolerance with no brownouts, USB disconnects, or ROS node resets.

Fail Criteria:
Voltage drops outside tolerance, devices reset, serial disconnects, or the Jetson reports undervoltage/power faults.

Notes:
Software cannot validate this without voltage telemetry; record measured values in the hardware log.

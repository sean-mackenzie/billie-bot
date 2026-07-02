import os
from glob import glob

from setuptools import setup


package_name = 'billiebot_tests'

console_scripts = [
    'test_motor_spin = billiebot_tests.test_motor_spin:main',
    'test_encoder_counts = billiebot_tests.test_encoder_counts:main',
    'test_lidar_scan = billiebot_tests.test_lidar_scan:main',
    'test_camera_oakd = billiebot_tests.test_camera_oakd:main',
    'test_audio_event = billiebot_tests.test_audio_event:main',
    'test_teleop_drive = billiebot_tests.test_teleop_drive:main',
    'test_forward_1m = billiebot_tests.test_forward_1m:main',
    'test_rotate_360 = billiebot_tests.test_rotate_360:main',
    'test_slam_map = billiebot_tests.test_slam_map:main',
    'test_localization_amcl = billiebot_tests.test_localization_amcl:main',
    'test_nav2_waypoint = billiebot_tests.test_nav2_waypoint:main',
    'test_search_route = billiebot_tests.test_search_route:main',
    'test_billie_visual_detection = billiebot_tests.test_billie_visual_detection:main',
    'test_bark_detection = billiebot_tests.test_bark_detection:main',
    'test_state_logging = billiebot_tests.test_state_logging:main',
    'test_daily_summary = billiebot_tests.test_daily_summary:main',
    'test_safety_stop = billiebot_tests.test_safety_stop:main',
]

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'manual'), glob('manual/*')),
        (os.path.join('share', package_name, 'scripts'), glob('scripts/*')),
    ],
    scripts=['scripts/run_mvp_smoke_tests.sh'],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='BillieBot Maintainers',
    maintainer_email='billiebot@example.com',
    description='Discrete verification scripts for BillieBot MVP bring-up.',
    license='MIT',
    entry_points={'console_scripts': console_scripts},
)

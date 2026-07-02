import os
from glob import glob

from setuptools import setup


package_name = 'billiebot_control'

data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
]

for root, _, files in os.walk('firmware'):
    paths = [os.path.join(root, f) for f in files]
    if paths:
        data_files.append((os.path.join('share', package_name, root), paths))

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='BillieBot Maintainers',
    maintainer_email='billiebot@example.com',
    description='Motor controller bridge and odometry for BillieBot.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'diff_drive_base = billiebot_control.diff_drive_base:main',
            'command_forward_1m = billiebot_control.command_forward_1m:main',
            'command_rotate_360 = billiebot_control.command_rotate_360:main',
            'report_odometry = billiebot_control.report_odometry:main',
        ],
    },
)

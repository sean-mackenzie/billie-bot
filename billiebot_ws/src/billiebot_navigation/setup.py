import os
from glob import glob

from setuptools import setup


package_name = 'billiebot_navigation'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='BillieBot Maintainers',
    maintainer_email='billiebot@example.com',
    description='Navigation configuration and deterministic search behavior for BillieBot.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'mock_lidar_node = billiebot_navigation.mock_lidar_node:main',
            'waypoint_search_node = billiebot_navigation.waypoint_search_node:main',
        ],
    },
)

import os
from glob import glob

from setuptools import setup


package_name = 'billiebot_perception'

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
    description='Visual perception nodes for BillieBot.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'billie_detector_node = billiebot_perception.billie_detector_node:main',
            'visual_state_node = billiebot_perception.visual_state_node:main',
            'mock_camera_node = billiebot_perception.mock_camera_node:main',
        ],
    },
)

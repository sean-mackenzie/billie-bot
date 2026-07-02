import os
from glob import glob

from setuptools import setup


package_name = 'billiebot_logging'

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
    description='SQLite event logging for BillieBot MVP observations.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'event_logger_node = billiebot_logging.event_logger_node:main',
        ],
    },
)

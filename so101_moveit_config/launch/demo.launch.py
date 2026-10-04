"""
demo.launch.py — MoveIt 2 Demo Launcher for SO-101 Follower Arm
Launches the full follower_moveit_demo bringup stack from so101_bringup.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # Include the main follower arm MoveIt 2 bringup launch file
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory("so101_bringup"),
                    "launch",
                    "follower_moveit_demo.launch.py",
                )
            )
        )
    ])

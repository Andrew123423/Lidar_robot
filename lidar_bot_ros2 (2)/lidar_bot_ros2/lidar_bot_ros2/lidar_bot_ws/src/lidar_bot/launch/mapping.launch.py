"""
launch/mapping.launch.py
────────────────────────
Запускает Gazebo + робот + slam_toolbox (онлайн-маппинг).
Используйте, чтобы построить карту simple_room перед локализацией.

Шаги:
  1. ros2 launch lidar_bot mapping.launch.py
  2. Управляйте роботом: ros2 run teleop_twist_keyboard teleop_twist_keyboard
  3. Когда карта готова, сохраните:
       ros2 run nav2_map_server map_saver_cli -f src/lidar_bot/maps/simple_room
  4. Перезапустите с основным launch-файлом:
       ros2 launch lidar_bot lidar_bot.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("lidar_bot")
    urdf_file  = os.path.join(pkg, "urdf",   "lidar_bot.urdf")
    world_file = os.path.join(pkg, "worlds", "simple_room.world")
    rviz_file  = os.path.join(pkg, "rviz",   "lidar_bot.rviz")
    slam_cfg   = os.path.join(pkg, "config", "slam_toolbox.yaml")

    with open(urdf_file, "r") as f:
        robot_description = f.read()

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("gazebo_ros"),
                "launch", "gazebo.launch.py",
            )
        ),
        launch_arguments={"world": world_file, "verbose": "false"}.items(),
    )

    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"use_sim_time": True, "robot_description": robot_description}],
    )

    spawn = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-entity", "lidar_bot", "-topic", "/robot_description",
                   "-x", "0.0", "-y", "0.0", "-z", "0.05"],
        output="screen",
    )

    slam = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[slam_cfg, {"use_sim_time": True}],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_file],
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription([
        gazebo, rsp, spawn,
        TimerAction(period=2.0, actions=[slam]),
        TimerAction(period=3.0, actions=[rviz]),
    ])

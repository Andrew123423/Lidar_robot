"""
launch/lidar_bot.launch.py
──────────────────────────
Запускает всё сразу:
  1. Gazebo с простым миром
  2. Публикация URDF (robot_state_publisher)
  3. Спавн робота в Gazebo
  4. map_server  — загружает готовую карту
  5. amcl        — локализация по лидару
  6. RViz2       — визуализация в 2D

Использование
─────────────
  ros2 launch lidar_bot lidar_bot.launch.py
  ros2 launch lidar_bot lidar_bot.launch.py map:=/путь/к/карте.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = get_package_share_directory("lidar_bot")

    # ── Пути к файлам ─────────────────────────────────────────────
    urdf_file   = os.path.join(pkg, "urdf",   "lidar_bot.urdf")
    world_file  = os.path.join(pkg, "worlds", "simple_room.world")
    rviz_file   = os.path.join(pkg, "rviz",   "lidar_bot.rviz")
    amcl_cfg    = os.path.join(pkg, "config", "amcl.yaml")

    # Карта по умолчанию — встроенная заглушка; можно передать свою
    default_map = os.path.join(pkg, "maps", "simple_room.yaml")

    with open(urdf_file, "r") as f:
        robot_description = f.read()

    # ── Аргументы запуска ─────────────────────────────────────────
    map_arg = DeclareLaunchArgument(
        "map",
        default_value=default_map,
        description="Путь к YAML-файлу карты для map_server",
    )

    # ── Gazebo ────────────────────────────────────────────────────
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("gazebo_ros"),
                "launch",
                "gazebo.launch.py",
            )
        ),
        launch_arguments={"world": world_file, "verbose": "false"}.items(),
    )

    # ── Robot State Publisher ─────────────────────────────────────
    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {"use_sim_time": True, "robot_description": robot_description}
        ],
    )

    # ── Spawn robot in Gazebo ─────────────────────────────────────
    spawn = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        name="spawn_robot",
        output="screen",
        arguments=[
            "-entity", "lidar_bot",
            "-topic", "/robot_description",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.05",
        ],
    )

    # ── Map Server ────────────────────────────────────────────────
    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"yaml_filename": LaunchConfiguration("map")},
        ],
    )

    # ── AMCL ──────────────────────────────────────────────────────
    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[amcl_cfg, {"use_sim_time": True}],
    )

    # ── Lifecycle Manager (активирует map_server + amcl) ─────────
    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"autostart": True},
            {"node_names": ["map_server", "amcl"]},
        ],
    )

    # ── RViz2 ─────────────────────────────────────────────────────
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_file],
        parameters=[{"use_sim_time": True}],
    )

    # ── Сборка ────────────────────────────────────────────────────
    return LaunchDescription(
        [
            map_arg,
            gazebo,
            rsp,
            spawn,
            # Даём Gazebo секунду подняться, потом стартуем nav2
            TimerAction(period=2.0, actions=[map_server, amcl, lifecycle_manager]),
            # RViz — через 3 с, чтобы карта и TF уже были готовы
            TimerAction(period=3.0, actions=[rviz]),
        ]
    )

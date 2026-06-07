# lidar_bot — простой 2D-лидарный робот на ROS 2 Humble

Минималистичный учебный пакет: робот с лазерным дальномером в симуляторе Gazebo, визуализация скана и карты в RViz, локализация через AMCL.

```
lidar_bot/
├── config/
│   ├── amcl.yaml            # параметры локализатора
│   └── slam_toolbox.yaml    # параметры маппера
├── launch/
│   ├── lidar_bot.launch.py  # 🚀 основной запуск (карта + AMCL + RViz)
│   └── mapping.launch.py    # 🗺️  построение карты (slam_toolbox)
├── maps/
│   └── simple_room.yaml     # метаданные карты
├── rviz/
│   └── lidar_bot.rviz       # готовая конфигурация RViz (2D, вид сверху)
├── urdf/
│   └── lidar_bot.urdf       # модель робота
└── worlds/
    └── simple_room.world    # мир Gazebo (комната 8×8 м)
```

---

## Зависимости

```bash
sudo apt update && sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-nav2-amcl \
  ros-humble-nav2-map-server \
  ros-humble-nav2-lifecycle-manager \
  ros-humble-slam-toolbox \
  ros-humble-robot-state-publisher \
  ros-humble-xacro \
  ros-humble-rviz2 \
  ros-humble-teleop-twist-keyboard
```

---

## Быстрый старт

### Шаг 1 — Сборка пакета

```bash
cd ~/lidar_bot_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### Шаг 2 — Вариант А: используем готовую карту с GitHub

Можно взять любую подходящую карту, например из репозитория nav2:

```bash
# Скачать пример карты
wget https://raw.githubusercontent.com/ros-planning/navigation2/main/nav2_bringup/maps/turtlebot3_world.yaml \
     -O ~/maps/map.yaml
wget https://raw.githubusercontent.com/ros-planning/navigation2/main/nav2_bringup/maps/turtlebot3_world.pgm \
     -O ~/maps/map.pgm

# Запустить с этой картой
ros2 launch lidar_bot lidar_bot.launch.py map:=$HOME/maps/map.yaml
```

> Если карта скачана для другого мира — в RViz будут видны расхождения между сканом и картой, но AMCL всё равно покажет принцип работы.

### Шаг 2 — Вариант Б: построить карту самому

```bash
# Терминал 1: запустить маппинг
ros2 launch lidar_bot mapping.launch.py

# Терминал 2: управление роботом клавиатурой
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Объезжаем комнату, пока карта не заполнится.

# Терминал 3: сохранить карту
ros2 run nav2_map_server map_saver_cli \
     -f src/lidar_bot/maps/simple_room
# Создаст simple_room.pgm + simple_room.yaml
```

### Шаг 3 — Запуск локализации

```bash
ros2 launch lidar_bot lidar_bot.launch.py
# или с явным путём к карте:
ros2 launch lidar_bot lidar_bot.launch.py map:=src/lidar_bot/maps/simple_room.yaml
```

---

## Что видно в RViz

| Слой | Описание |
|------|----------|
| **Map** | Занятая/свободная карта (серый = неизвестно, белый = свободно, чёрный = стена) |
| **LaserScan** | Текущие лучи лидара (красные точки) |
| **AMCL Particles** | Облако гипотез о позиции робота (голубые стрелки) |
| **Estimated Pose** | Лучшая оценка позы (оранжевая стрелка) |
| **RobotModel** | 3D-модель робота |
| **Odometry** | След одометрии |

---

## Управление роботом вручную

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Клавиши: `i` — вперёд, `,` — назад, `j`/`l` — поворот, `k` — стоп.

---

## Архитектура топиков

```
Gazebo
  │
  ├─► /scan          (sensor_msgs/LaserScan)   — данные лидара
  ├─► /odom          (nav_msgs/Odometry)        — одометрия колёс
  └─► /robot_description  — URDF модель

map_server
  └─► /map           (nav_msgs/OccupancyGrid)  — загруженная карта

amcl
  ├─◄ /scan, /map, /odom
  ├─► /amcl_pose     (geometry_msgs/PoseWithCovarianceStamped)
  ├─► /particle_cloud (geometry_msgs/PoseArray) — частицы фильтра
  └─► TF: map → odom → base_link

teleop_twist_keyboard
  └─► /cmd_vel       (geometry_msgs/Twist)     — команды движения
```

---

## Как работает AMCL (кратко)

1. **Инициализация**: 500–2000 частиц равномерно рассеяны по карте — каждая = гипотеза о позиции робота.
2. **Предсказание**: при движении робота частицы смещаются с учётом шума одометрии.
3. **Обновление весов**: каждая частица оценивается: насколько её предсказанный скан совпадает с реальным `/scan`.
4. **Ресэмплинг**: частицы с высоким весом «размножаются», слабые отбрасываются → облако сходится к истинной позиции.
5. **Выход**: лучшая оценка публикуется в `/amcl_pose` и TF `map→odom`.

---

## Частые проблемы

**Gazebo не видит URDF плагины**
```bash
source /usr/share/gazebo/setup.sh
```

**AMCL не конвергирует**
Уточните начальную позу через RViz: кнопка «2D Pose Estimate» (сверху) → клик на карте.

**Нет карты в RViz**
Проверьте, что lifecycle_manager активировал map_server:
```bash
ros2 node list | grep map_server
ros2 lifecycle get /map_server
```

---

## Лицензия

MIT

# Counter-UAS System — ROS 2 Simulation
A full **detect → classify → intercept** pipeline for counter-drone operations, built in ROS 2.
## Architecture
```
┌─────────────────────────────────────────────────────┐
│                  COUNTER-UAS PIPELINE                │
│                                                      │
│  [Intruder Drone] ──pose──▶ [Radar Detector]        │
│                                    │                 │
│                               detection              │
│                                    │                 │
│                                    ▼                 │
│                          [Threat Classifier]         │
│                                    │                 │
│                            HOSTILE/FRIENDLY          │
│                                    │                 │
│                                    ▼                 │
│                          [Interceptor Drone]         │
│                          Pure Pursuit Controller     │
│                                    │                 │
│                                    ▼                 │
│                         [Mission Controller]         │
│                           Live Dashboard             │
└─────────────────────────────────────────────────────┘
```
## ROS 2 Topics
| Topic | Type | Description |
|---|---|---|
| `/intruder/pose` | PoseStamped | Ground truth intruder position |
| `/intruder/velocity` | TwistStamped | Intruder velocity |
| `/radar/detection` | PoseStamped | Noisy radar detection |
| `/radar/alert` | String | Range + SNR data |
| `/classifier/threat` | String | HOSTILE/FRIENDLY + confidence |
| `/interceptor/pose` | PoseStamped | Defender drone position |
| `/interceptor/status` | String | State machine status |
| `/mission/summary` | String | Aggregated mission log |
## Prerequisites
- Ubuntu 22.04
- ROS 2 Jazzy
- Python 3.10+
```bash
sudo apt install ros-jazzy-desktop ros-humble-launch-ros
```
## Build & Run
```bash
# 1. Clone / copy this package into your workspace
git clone https://github.com/saravanaperumal209/counter-uas-ros2.git
cd counter-uas-ros2
# 2. Build
source /opt/ros/jazzy/setup.bash
colcon build --packages-select counter_uas
source install/setup.bash
# 3. Launch everything
ros2 launch counter_uas counter_uas_launch.py
```
## Visualise in RViz
```bash
# In a second terminal
source ~/ros2_ws/install/setup.bash
rviz2 -d src/counter_uas/config/counter_uas.rviz
```
## What to add to visualize drone paths in RViz
Add these display types manually in RViz:
- **Path** → topic `/intruder/pose` (set history length 200)
- **Path** → topic `/interceptor/pose` (set history length 200)
- **Marker** → topic `/interceptor/marker`
# Project Structure
```
counter_uas/
├── counter_uas/
│   ├── intruder_drone.py       # Simulated hostile drone
│   ├── radar_detector.py       # Radar sensor simulation
│   ├── threat_classifier.py    # Detect → classify logic
│   ├── interceptor_drone.py    # Pure pursuit interceptor
│   └── mission_controller.py  # Dashboard + orchestration
├── launch/
│   └── counter_uas_launch.py
├── config/
│   └── counter_uas.rviz
├── CMakeLists.txt
└── package.xml
```
## Threat Classification Logic
The classifier scores targets on:
| Feature | Weight |
|---|---|
| Speed > 15 m/s | +35 pts |
| Proximity < 20 m | +35 pts |
| Erratic heading | +20 pts |
| Low SNR (<5 dB) | ×0.5 penalty |
Score ≥ 70 → `HOSTILE / CRITICAL`  
Score ≥ 45 → `HOSTILE / HIGH`  
Score ≥ 25 → `SUSPICIOUS / MEDIUM`
## Extending This Project
- **Add YOLO-based visual detection** — subscribe to a camera topic, run inference, fuse with radar
- **Swap rule-based classifier for a trained model** — use scikit-learn or PyTorch
- **Add geofence** — trigger alerts when intruder crosses a defined boundary polygon
- **Multi-intruder** — spawn 3 intruders, assign interceptors via Hungarian algorithm
- **PX4 integration** — replace simulated pose with actual MAVLink commands
##  Author 
**Saravana Perumal K**
MSc Mechatronics & IT — Karlsruhe Institute of Technology (KIT)
[![LinkedIn](https://www.linkedin.com/in/saravana-perumal-k)
[![GitHub](https://github.com/saravanaperumal209)

---


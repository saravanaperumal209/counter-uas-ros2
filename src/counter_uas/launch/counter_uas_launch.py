"""
counter_uas_launch.py
---------------------
Launches all 4 nodes of the Counter-UAS pipeline:
  1. intruder_drone       — simulates hostile drone
  2. radar_detector       — detects intruder, adds noise
  3. threat_classifier    — classifies as HOSTILE/FRIENDLY
  4. interceptor_drone    — pursues and intercepts
  5. mission_controller   — dashboard + orchestration
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction


def generate_launch_description():
    intruder = Node(
        package='counter_uas',
        executable='intruder_drone.py',
        name='intruder_drone',
        output='screen',
        emulate_tty=True,
    )

    radar = Node(
        package='counter_uas',
        executable='radar_detector.py',
        name='radar_detector',
        output='screen',
        emulate_tty=True,
    )

    classifier = Node(
        package='counter_uas',
        executable='threat_classifier.py',
        name='threat_classifier',
        output='screen',
        emulate_tty=True,
    )

    # Interceptor starts 2s after classifier so first classifications are ready
    interceptor = TimerAction(
        period=2.0,
        actions=[Node(
            package='counter_uas',
            executable='interceptor_drone.py',
            name='interceptor_drone',
            output='screen',
            emulate_tty=True,
        )]
    )

    controller = TimerAction(
        period=1.0,
        actions=[Node(
            package='counter_uas',
            executable='mission_controller.py',
            name='mission_controller',
            output='screen',
            emulate_tty=True,
        )]
    ) 
    visualizer = TimerAction(
    period=3.0,
    actions=[Node(
        package='counter_uas',
        executable='drone_visualizer.py',
        name='drone_visualizer',
        output='screen',
        emulate_tty=True,
    )] 
    )

    return LaunchDescription([
        intruder,
        radar,
        classifier,
        interceptor,
        controller, 
        visualizer,
    ])

#!/usr/bin/env python3
"""
Mission Controller Node
------------------------
Top-level orchestrator. Subscribes to all nodes and prints a
live ASCII dashboard to the terminal — great for screen-recording
your LinkedIn demo!

Also publishes a /mission/summary topic for logging.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
import time
import math


class MissionController(Node):
    def __init__(self):
        super().__init__('mission_controller')

        # Subscriptions
        self.create_subscription(String,      '/radar/alert',         self.radar_cb,       10)
        self.create_subscription(String,      '/classifier/threat',   self.classifier_cb,  10)
        self.create_subscription(String,      '/interceptor/status',  self.interceptor_cb, 10)
        self.create_subscription(PoseStamped, '/intruder/pose',        self.intruder_cb,    10)
        self.create_subscription(PoseStamped, '/interceptor/pose',     self.defender_cb,    10)

        # Publisher
        self.summary_pub = self.create_publisher(String, '/mission/summary', 10)

        # Dashboard state
        self.radar_status       = 'Scanning...'
        self.threat_label       = 'UNKNOWN'
        self.threat_level       = 'LOW'
        self.threat_conf        = 0.0
        self.interceptor_state  = 'STANDBY'
        self.intercepts         = 0
        self.intruder_pos       = (0.0, 0.0, 0.0)
        self.defender_pos       = (0.0, 0.0, 0.0)
        self.mission_start      = time.time()

        self.dashboard_timer = self.create_timer(1.0, self.print_dashboard)
        self.get_logger().info('🎯 Mission controller started')

    def radar_cb(self, msg: String):
        self.radar_status = msg.data

    def classifier_cb(self, msg: String):
        parts = msg.data.split('|')
        self.threat_label = parts[0]
        for p in parts[1:]:
            if p.startswith('level='):   self.threat_level = p.split('=')[1]
            if p.startswith('conf='):    self.threat_conf  = float(p.split('=')[1])

    def interceptor_cb(self, msg: String):
        parts = msg.data.split('|')
        self.interceptor_state = parts[0]
        for p in parts[1:]:
            if p.startswith('intercepts='):
                self.intercepts = int(p.split('=')[1])

    def intruder_cb(self, msg: PoseStamped):
        p = msg.pose.position
        self.intruder_pos = (p.x, p.y, p.z)

    def defender_cb(self, msg: PoseStamped):
        p = msg.pose.position
        self.defender_pos = (p.x, p.y, p.z)

    def _separation(self):
        ix, iy, iz = self.intruder_pos
        dx, dy, dz = self.defender_pos
        return math.sqrt((ix-dx)**2 + (iy-dy)**2 + (iz-dz)**2)

    def _threat_color(self):
        colors = {'HOSTILE': '🔴', 'SUSPICIOUS': '🟡', 'FRIENDLY': '🟢', 'UNKNOWN': '⚪'}
        return colors.get(self.threat_label, '⚪')

    def print_dashboard(self):
        elapsed = int(time.time() - self.mission_start)
        sep = self._separation()
        mm, ss = divmod(elapsed, 60)

        print('\033[2J\033[H', end='')  # Clear terminal
        print('╔══════════════════════════════════════════════════════╗')
        print('║          COUNTER-UAS MISSION CONTROL                 ║')
        print('╠══════════════════════════════════════════════════════╣')
        print(f'║  Mission time : {mm:02d}:{ss:02d}                                  ║')
        print(f'║  Intercepts   : {self.intercepts}                                      ║')
        print('╠══════════════════════════════════════════════════════╣')
        print('║  📡 RADAR                                            ║')
        print(f'║  Status : {self.radar_status[:45]:<45}  ║')
        print('╠══════════════════════════════════════════════════════╣')
        print('║  🧠 THREAT CLASSIFICATION                            ║')
        print(f'║  Label  : {self._threat_color()} {self.threat_label:<10}  Level: {self.threat_level:<8}       ║')
        print(f'║  Conf   : {self.threat_conf:.0%}                                      ║')
        print('╠══════════════════════════════════════════════════════╣')
        print('║  🛸 INTRUDER                                         ║')
        ix, iy, iz = self.intruder_pos
        print(f'║  Pos    : ({ix:6.1f}, {iy:6.1f}, {iz:5.1f}) m                  ║')
        print('╠══════════════════════════════════════════════════════╣')
        print('║  🚁 INTERCEPTOR                                      ║')
        print(f'║  State  : {self.interceptor_state:<15}                        ║')
        dx, dy, dz = self.defender_pos
        print(f'║  Pos    : ({dx:6.1f}, {dy:6.1f}, {dz:5.1f}) m                  ║')
        print(f'║  Sep    : {sep:6.1f} m from intruder                       ║')
        print('╚══════════════════════════════════════════════════════╝')

        # Publish summary
        summary = String()
        summary.data = (
            f'time={elapsed}|threat={self.threat_label}|level={self.threat_level}|'
            f'state={self.interceptor_state}|intercepts={self.intercepts}|sep={sep:.1f}'
        )
        self.summary_pub.publish(summary)


def main(args=None):
    rclpy.init(args=args)
    node = MissionController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

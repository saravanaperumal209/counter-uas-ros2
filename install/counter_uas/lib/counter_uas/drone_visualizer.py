#!/usr/bin/env python3
"""
Drone Visualizer Node
----------------------
Publishes:
  - MarkerArray with quadrotor shape for BOTH drones
  - nav_msgs/Path for intruder (red) and interceptor (blue)
  - Yellow flash marker on intercept event
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import String
import math

MAX_PATH_LENGTH = 500


class DroneVisualizer(Node):
    def __init__(self):
        super().__init__('drone_visualizer')

        self.create_subscription(PoseStamped, '/intruder/pose',     self.intruder_cb,    10)
        self.create_subscription(PoseStamped, '/interceptor/pose',  self.interceptor_cb, 10)
        self.create_subscription(String,      '/interceptor/status', self.status_cb,     10)
        self.create_subscription(String,      '/classifier/threat',  self.threat_cb,     10)

        self.intruder_marker_pub    = self.create_publisher(MarkerArray, '/viz/intruder_drone',    10)
        self.interceptor_marker_pub = self.create_publisher(MarkerArray, '/viz/interceptor_drone', 10)
        self.intruder_path_pub      = self.create_publisher(Path,        '/viz/intruder_path',     10)
        self.interceptor_path_pub   = self.create_publisher(Path,        '/viz/interceptor_path',  10)
        self.event_marker_pub       = self.create_publisher(Marker,      '/viz/event_marker',      10)

        self.intruder_pose         = None
        self.interceptor_pose      = None
        self.interceptor_state     = 'STANDBY'
        self.threat_label          = 'UNKNOWN'
        self.intruder_path         = Path()
        self.interceptor_path      = Path()
        self.intruder_path.header.frame_id    = 'world'
        self.interceptor_path.header.frame_id = 'world'
        self.intercept_flash_count = 0

        self.create_timer(0.1, self.publish_all)
        self.get_logger().info('🎨 Drone visualizer online')

    def intruder_cb(self, msg):
        self.intruder_pose = msg
        msg.header.frame_id = 'world'
        self.intruder_path.poses.append(msg)
        if len(self.intruder_path.poses) > MAX_PATH_LENGTH:
            self.intruder_path.poses.pop(0)

    def interceptor_cb(self, msg):
        self.interceptor_pose = msg
        msg.header.frame_id = 'world'
        self.interceptor_path.poses.append(msg)
        if len(self.interceptor_path.poses) > MAX_PATH_LENGTH:
            self.interceptor_path.poses.pop(0)

    def status_cb(self, msg):
        self.interceptor_state = msg.data.split('|')[0]
        if self.interceptor_state == 'INTERCEPTED':
            self.intercept_flash_count = 10

    def threat_cb(self, msg):
        self.threat_label = msg.data.split('|')[0]

    def _quadrotor_markers(self, pose, drone_id, is_hostile):
        now = self.get_clock().now().to_msg()
        x = pose.pose.position.x
        y = pose.pose.position.y
        z = pose.pose.position.z
        markers = MarkerArray()

        if is_hostile:
            body_color  = (0.9, 0.15, 0.15, 1.0)
            rotor_color = (0.7, 0.1,  0.1,  0.8)
            arm_color   = (0.6, 0.1,  0.1,  1.0)
        else:
            if self.interceptor_state == 'PURSUING':
                body_color = (0.1, 0.8, 1.0, 1.0)
            elif self.interceptor_state == 'STANDBY':
                body_color = (0.2, 0.9, 0.2, 1.0)
            else:
                body_color = (0.1, 0.5, 1.0, 1.0)
            rotor_color = (0.1, 0.3, 0.8, 0.8)
            arm_color   = (0.1, 0.3, 0.7, 1.0)

        def make_marker(uid, mtype, sx, sy, sz, ox, oy, oz, color):
            m = Marker()
            m.header.frame_id = 'world'
            m.header.stamp = now
            m.ns = f'drone_{drone_id}'
            m.id = uid
            m.type = mtype
            m.action = Marker.ADD
            m.pose.position.x = x + ox
            m.pose.position.y = y + oy
            m.pose.position.z = z + oz
            m.pose.orientation.w = 1.0
            m.scale.x, m.scale.y, m.scale.z = sx, sy, sz
            m.color.r, m.color.g, m.color.b, m.color.a = color
            m.lifetime.nanosec = 200_000_000
            return m

        # Body
        markers.markers.append(
            make_marker(drone_id*20+0, Marker.CUBE,
                        3.0, 3.0, 0.8, 0, 0, 0, body_color))

        # 4 Arms
        arm_offsets = [(0.9, 0.9), (0.9, -0.9), (-0.9, 0.9), (-0.9, -0.9)]
        for i, (ax, ay) in enumerate(arm_offsets):
            m = make_marker(drone_id*20+1+i, Marker.CUBE,
                            2.2, 0.4, 0.3, ax, ay, 0, arm_color)
            m.pose.orientation.z = 0.383
            m.pose.orientation.w = 0.924
            markers.markers.append(m)

        # 4 Rotors
        rotor_offsets = [(1.6, 1.6), (1.6, -1.6), (-1.6, 1.6), (-1.6, -1.6)]
        for i, (rx, ry) in enumerate(rotor_offsets):
            markers.markers.append(
                make_marker(drone_id*20+5+i, Marker.CYLINDER,
                            2.0, 2.0, 0.15, rx, ry, 0.3, rotor_color))

        return markers

    def _intercept_flash(self, x, y, z):
        m = Marker()
        m.header.frame_id = 'world'
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'event'
        m.id = 999
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position.x = x
        m.pose.position.y = y
        m.pose.position.z = z
        m.pose.orientation.w = 1.0
        size = 4.0 + 2.0 * math.sin(self.intercept_flash_count * 0.8)
        m.scale.x = m.scale.y = m.scale.z = size
        m.color.r, m.color.g, m.color.b, m.color.a = 1.0, 0.8, 0.0, 0.7
        m.lifetime.nanosec = 300_000_000
        return m

    def publish_all(self):
        now = self.get_clock().now().to_msg()

        if self.intruder_pose:
            self.intruder_marker_pub.publish(
                self._quadrotor_markers(self.intruder_pose, 1, True))

        if self.interceptor_pose:
            self.interceptor_marker_pub.publish(
                self._quadrotor_markers(self.interceptor_pose, 2, False))

        self.intruder_path.header.stamp    = now
        self.interceptor_path.header.stamp = now
        self.intruder_path_pub.publish(self.intruder_path)
        self.interceptor_path_pub.publish(self.interceptor_path)

        if self.intercept_flash_count > 0 and self.interceptor_pose:
            p = self.interceptor_pose.pose.position
            self.event_marker_pub.publish(self._intercept_flash(p.x, p.y, p.z))
            self.intercept_flash_count -= 1


def main(args=None):
    rclpy.init(args=args)
    node = DroneVisualizer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

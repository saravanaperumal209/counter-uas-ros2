#!/usr/bin/env python3
"""
Interceptor Drone Node
-----------------------
Defender drone that:
  1. Waits on standby at home position
  2. On HOSTILE classification → launches and pursues using Pure Pursuit
  3. On intercept (within 2m) → logs success, returns home

States: STANDBY → LAUNCHING → PURSUING → INTERCEPTED → RETURNING → STANDBY
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from visualization_msgs.msg import Marker
import math


HOME_POS   = (0.0, 0.0, 3.0)    # Defender home base
MAX_SPEED  = 12.0                 # m/s — faster than intruder
INTERCEPT_RADIUS = 2.5            # metres — "kill zone"


class InterceptorDrone(Node):
    def __init__(self):
        super().__init__('interceptor_drone')

        # Subscriptions
        self.create_subscription(String,      '/classifier/threat', self.threat_cb,   10)
        self.create_subscription(PoseStamped, '/radar/detection',   self.detection_cb, 10)

        # Publishers
        self.pose_pub   = self.create_publisher(PoseStamped, '/interceptor/pose',   10)
        self.status_pub = self.create_publisher(String,      '/interceptor/status', 10)
        self.marker_pub = self.create_publisher(Marker,      '/interceptor/marker', 10)

        # State
        self.x, self.y, self.z = HOME_POS
        self.state      = 'STANDBY'
        self.target     = None   # (x, y, z) of intruder from radar
        self.intercepts = 0
        self.dt         = 0.1

        self.timer = self.create_timer(self.dt, self.update)
        self.get_logger().info(f'🚁 Interceptor ready at {HOME_POS} | state=STANDBY')

    def threat_cb(self, msg: String):
        parts = msg.data.split('|')
        label = parts[0]
        if label == 'HOSTILE' and self.state == 'STANDBY':
            self.state = 'LAUNCHING'
            self.get_logger().info('🚨 HOSTILE confirmed → LAUNCHING interceptor!')

    def detection_cb(self, msg: PoseStamped):
        p = msg.pose.position
        self.target = (p.x, p.y, p.z)

    def _move_toward(self, tx, ty, tz, speed):
        """Pure pursuit step — move toward target at given speed."""
        dx, dy, dz = tx - self.x, ty - self.y, tz - self.z
        dist = math.sqrt(dx**2 + dy**2 + dz**2)
        if dist < 0.1:
            return dist
        scale = min(speed, dist / self.dt) / dist
        self.x += dx * scale * self.dt
        self.y += dy * scale * self.dt
        self.z += dz * scale * self.dt
        self.z  = max(1.0, self.z)
        return dist

    def update(self):
        # ── State machine ───────────────────────────────────────────────
        if self.state == 'STANDBY':
            pass  # Hover at home

        elif self.state == 'LAUNCHING':
            # Rise to operating altitude first
            dist = self._move_toward(self.x, self.y, 15.0, MAX_SPEED * 0.5)
            if dist < 1.0:
                self.state = 'PURSUING'
                self.get_logger().info('🔼 Altitude reached → PURSUING')

        elif self.state == 'PURSUING':
            if self.target is None:
                return
            tx, ty, tz = self.target
            dist = self._move_toward(tx, ty, tz, MAX_SPEED)
            self.get_logger().debug(
                f'Pursuing | dist={dist:.1f}m | pos=({self.x:.1f},{self.y:.1f},{self.z:.1f})'
            )
            if dist < INTERCEPT_RADIUS:
                self.state = 'INTERCEPTED'
                self.intercepts += 1
                self.get_logger().info(
                    f'💥 INTERCEPT #{self.intercepts} at ({self.x:.1f},{self.y:.1f},{self.z:.1f})'
                )

        elif self.state == 'INTERCEPTED':
            self.state = 'RETURNING'
            self.get_logger().info('↩️  Returning to base...')

        elif self.state == 'RETURNING':
            hx, hy, hz = HOME_POS
            dist = self._move_toward(hx, hy, hz, MAX_SPEED * 0.7)
            if dist < 1.0:
                self.state = 'STANDBY'
                self.get_logger().info('🏠 Back at base | state=STANDBY')

        # ── Publish pose ─────────────────────────────────────────────────
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = 'world'
        pose.pose.position.x = self.x
        pose.pose.position.y = self.y
        pose.pose.position.z = self.z
        self.pose_pub.publish(pose)

        # ── Publish status ────────────────────────────────────────────────
        status = String()
        status.data = (
            f'{self.state}|pos={self.x:.2f},{self.y:.2f},{self.z:.2f}|'
            f'intercepts={self.intercepts}'
        )
        self.status_pub.publish(status)

        # ── RViz marker (blue sphere) ─────────────────────────────────────
        marker = Marker()
        marker.header.frame_id = 'world'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'interceptor'
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose.position.x = self.x
        marker.pose.position.y = self.y
        marker.pose.position.z = self.z
        marker.scale.x = marker.scale.y = marker.scale.z = 1.5
        marker.color.a = 1.0
        marker.color.r = 0.0
        marker.color.g = 0.4
        marker.color.b = 1.0
        self.marker_pub.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    node = InterceptorDrone()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

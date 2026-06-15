#!/usr/bin/env python3
"""
Intruder Drone Node
-------------------
Simulates a hostile drone flying random waypoints inside a restricted zone.
Publishes its pose so the radar detector can pick it up.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TwistStamped
from std_msgs.msg import String
import math
import random


class IntruderDrone(Node):
    def __init__(self):
        super().__init__('intruder_drone')

        # Publishers
        self.pose_pub = self.create_publisher(PoseStamped, '/intruder/pose', 10)
        self.twist_pub = self.create_publisher(TwistStamped, '/intruder/velocity', 10)
        self.status_pub = self.create_publisher(String, '/intruder/status', 10)

        # State
        self.x = random.uniform(-20.0, 20.0)
        self.y = random.uniform(-20.0, 20.0)
        self.z = random.uniform(5.0, 30.0)
        self.speed = random.uniform(10.0, 18.0)  # m/s — vary for classification
        self.waypoints = self._generate_waypoints(8)
        self.current_wp = 0
        self.dt = 0.1  # 10 Hz

        self.timer = self.create_timer(self.dt, self.update)
        self.get_logger().info(
            f'🛸 Intruder drone spawned at ({self.x:.1f}, {self.y:.1f}, {self.z:.1f}) '
            f'| speed={self.speed:.1f} m/s'
        )

    def _generate_waypoints(self, n):
        """Random waypoints inside a 100x100m restricted zone."""
        return [
            (random.uniform(-40.0, 40.0),
             random.uniform(-40.0, 40.0),
             random.uniform(5.0, 40.0))
            for _ in range(n)
        ]

    def update(self):
        if self.current_wp >= len(self.waypoints):
            self.waypoints = self._generate_waypoints(8)
            self.current_wp = 0

        tx, ty, tz = self.waypoints[self.current_wp]
        dx, dy, dz = tx - self.x, ty - self.y, tz - self.z
        dist = math.sqrt(dx**2 + dy**2 + dz**2)

        if dist < 1.5:
            self.current_wp += 1
            return

        # Move toward waypoint
        norm = dist
        vx = (dx / norm) * self.speed
        vy = (dy / norm) * self.speed
        vz = (dz / norm) * self.speed * 0.3

        self.x += vx * self.dt
        self.y += vy * self.dt
        self.z += vz * self.dt
        self.z = max(1.0, self.z)  # Don't go underground

        # Publish pose
        pose_msg = PoseStamped()
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        pose_msg.header.frame_id = 'world'
        pose_msg.pose.position.x = self.x
        pose_msg.pose.position.y = self.y
        pose_msg.pose.position.z = self.z
        self.pose_pub.publish(pose_msg)

        # Publish velocity
        twist_msg = TwistStamped()
        twist_msg.header.stamp = self.get_clock().now().to_msg()
        twist_msg.twist.linear.x = vx
        twist_msg.twist.linear.y = vy
        twist_msg.twist.linear.z = vz
        self.twist_pub.publish(twist_msg)

        # Status
        status = String()
        status.data = f'FLYING|{self.x:.2f},{self.y:.2f},{self.z:.2f}|wp={self.current_wp}'
        self.status_pub.publish(status)


def main(args=None):
    rclpy.init(args=args)
    node = IntruderDrone()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Radar Detector Node
--------------------
Simulates a radar system that detects drones within range.
Adds realistic Gaussian noise to simulate sensor imperfection.
Publishes detections with SNR (signal-to-noise ratio) for the classifier.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import math
import random


RADAR_RANGE_M   = 300.0  # Max detection range in metres
RADAR_ORIGIN    = (0.0, 0.0, 0.0)
POSITION_NOISE  = 0.8     # Gaussian noise std-dev (metres)
DETECTION_RATE  = 0.92    # Probability of detecting a target per cycle (miss rate 8%)


class RadarDetector(Node):
    def __init__(self):
        super().__init__('radar_detector')

        # Subscribe to intruder ground truth
        self.sub = self.create_subscription(
            PoseStamped, '/intruder/pose', self.pose_callback, 10)

        # Publishers
        self.detection_pub = self.create_publisher(PoseStamped, '/radar/detection', 10)
        self.alert_pub     = self.create_publisher(String,      '/radar/alert',     10)

        self.detection_count = 0
        self.get_logger().info('📡 Radar detector online | range=%.0f m' % RADAR_RANGE_M)

    def pose_callback(self, msg: PoseStamped):
        ix = msg.pose.position.x
        iy = msg.pose.position.y
        iz = msg.pose.position.z

        ox, oy, oz = RADAR_ORIGIN
        range_m = math.sqrt((ix-ox)**2 + (iy-oy)**2 + (iz-oz)**2)

        # Out of range → no detection
        if range_m > RADAR_RANGE_M:
            return

        # Probabilistic miss
        if random.random() > DETECTION_RATE:
            self.get_logger().debug('Radar miss (stochastic)')
            return

        # Add sensor noise
        noisy_x = ix + random.gauss(0, POSITION_NOISE)
        noisy_y = iy + random.gauss(0, POSITION_NOISE)
        noisy_z = iz + random.gauss(0, POSITION_NOISE * 0.5)

        # SNR decreases with range (free-space path loss model)
        snr_db = 30.0 - 20.0 * math.log10(max(range_m, 1.0) / 10.0)

        # Publish noisy detection
        det = PoseStamped()
        det.header.stamp = self.get_clock().now().to_msg()
        det.header.frame_id = 'world'
        det.pose.position.x = noisy_x
        det.pose.position.y = noisy_y
        det.pose.position.z = noisy_z
        self.detection_pub.publish(det)

        # Alert string carries range + SNR for classifier
        alert = String()
        alert.data = (
            f'DETECTED|range={range_m:.1f}|snr={snr_db:.1f}|'
            f'pos={noisy_x:.2f},{noisy_y:.2f},{noisy_z:.2f}'
        )
        self.alert_pub.publish(alert)

        self.detection_count += 1
        if self.detection_count % 50 == 0:
            self.get_logger().info(
                f'📡 {self.detection_count} detections | last range={range_m:.1f}m | SNR={snr_db:.1f}dB'
            )


def main(args=None):
    rclpy.init(args=args)
    node = RadarDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

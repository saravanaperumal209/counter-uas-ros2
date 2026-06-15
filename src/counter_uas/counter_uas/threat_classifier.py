#!/usr/bin/env python3
"""
Threat Classifier Node
-----------------------
Rule-based + heuristic classifier that mimics a lightweight ML pipeline.
Inputs:
  - Radar detections (position stream)
  - Intruder velocity (ground truth for demo; in real life this comes from track filter)
Outputs:
  - Threat classification: HOSTILE / FRIENDLY / UNKNOWN
  - Confidence score 0–1
  - Threat level: LOW / MEDIUM / HIGH / CRITICAL

Classification logic (simplified decision tree):
  1. Speed  > 12 m/s           → HIGH threat indicator
  2. Zone   < 30 m from origin → CRITICAL proximity
  3. SNR    < 5 dB             → UNKNOWN (low confidence)
  4. Erratic heading changes   → HOSTILE indicator
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TwistStamped
from std_msgs.msg import String
import math
from collections import deque


class ThreatClassifier(Node):
    def __init__(self):
        super().__init__('threat_classifier')

        # Subscriptions
        self.create_subscription(PoseStamped, '/radar/detection',   self.detection_cb, 10)
        self.create_subscription(TwistStamped, '/intruder/velocity', self.velocity_cb,  10)
        self.create_subscription(String,       '/radar/alert',       self.alert_cb,     10)

        # Publisher
        self.threat_pub = self.create_publisher(String, '/classifier/threat', 10)

        # State tracking
        self.speed         = 0.0
        self.snr_db        = 30.0
        self.range_m       = 0.0
        self.pos_history   = deque(maxlen=10)   # Track last 10 positions
        self.last_threat   = 'UNKNOWN'
        self.classify_timer = self.create_timer(0.5, self.classify)

        self.get_logger().info('🧠 Threat classifier online')

    def detection_cb(self, msg: PoseStamped):
        p = msg.pose.position
        self.pos_history.append((p.x, p.y, p.z))
        self.range_m = math.sqrt(p.x**2 + p.y**2 + p.z**2)

    def velocity_cb(self, msg: TwistStamped):
        v = msg.twist.linear
        self.speed = math.sqrt(v.x**2 + v.y**2 + v.z**2)

    def alert_cb(self, msg: String):
        parts = msg.data.split('|')
        for part in parts:
            if part.startswith('snr='):
                self.snr_db = float(part.split('=')[1])
            elif part.startswith('range='):
                self.range_m = float(part.split('=')[1])

    def _heading_variance(self):
        """Compute heading change variance — erratic = hostile indicator."""
        if len(self.pos_history) < 3:
            return 0.0
        angles = []
        hist = list(self.pos_history)
        for i in range(1, len(hist)):
            dx = hist[i][0] - hist[i-1][0]
            dy = hist[i][1] - hist[i-1][1]
            angles.append(math.atan2(dy, dx))
        if len(angles) < 2:
            return 0.0
        diffs = [abs(angles[i] - angles[i-1]) for i in range(1, len(angles))]
        return sum(diffs) / len(diffs)

    def classify(self):
        if not self.pos_history:
            return

        # ── Feature extraction ──────────────────────────────────────────
        heading_var   = self._heading_variance()
        proximity     = self.range_m
        speed         = self.speed
        snr           = self.snr_db

        # ── Scoring (additive threat score 0–100) ───────────────────────
        score = 0.0

        # Speed scoring
        if speed > 15.0:
            score += 35
        elif speed > 8.0:
            score += 20
        elif speed > 3.0:
            score += 10

        # Proximity scoring
        if proximity < 20.0:
            score += 35
        elif proximity < 50.0:
            score += 20
        elif proximity < 100.0:
            score += 10

        # Erratic behaviour
        if heading_var > 0.8:
            score += 20
        elif heading_var > 0.4:
            score += 10

        # Low SNR → uncertain, reduce score
        if snr < 5.0:
            score *= 0.5

        # ── Classify ────────────────────────────────────────────────────
        confidence = min(score / 90.0, 1.0)

        if snr < 3.0:
            label, level = 'UNKNOWN', 'LOW'
        elif score >= 70:
            label, level = 'HOSTILE', 'CRITICAL'
        elif score >= 45:
            label, level = 'HOSTILE', 'HIGH'
        elif score >= 25:
            label, level = 'SUSPICIOUS', 'MEDIUM'
        else:
            label, level = 'FRIENDLY', 'LOW'

        self.last_threat = label

        msg = String()
        msg.data = (
            f'{label}|level={level}|conf={confidence:.2f}|'
            f'speed={speed:.1f}|range={proximity:.1f}|snr={snr:.1f}|'
            f'heading_var={heading_var:.2f}'
        )
        self.threat_pub.publish(msg)

        if label in ('HOSTILE', 'SUSPICIOUS'):
            self.get_logger().warn(
                f'⚠️  [{level}] {label} | conf={confidence:.0%} | '
                f'speed={speed:.1f}m/s range={proximity:.0f}m'
            )


def main(args=None):
    rclpy.init(args=args)
    node = ThreatClassifier()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

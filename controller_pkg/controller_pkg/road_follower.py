#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge, CvBridgeError

import cv2

from controller_pkg.road_detector import detect_road


class RoadFollower(Node):

    def __init__(self):

        super().__init__('road_follower')

        self.bridge = CvBridge()

        # Subscribe to camera
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.camera_callback,
            1
        )

        # Publish robot velocity
        self.velocity_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # Controller parameters
        self.Kp = 0.005
        self.linear_speed = 0.15
        self.max_angular_speed = 0.8

        self.get_logger().info(
            "Road follower initialized"
        )

    def camera_callback(self, msg):

        try:
            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='bgr8'
            )

        except CvBridgeError as e:
            self.get_logger().error(str(e))
            return

        # Detect road
        error, debug_frame, mask = detect_road(frame)

        move = Twist()

        if error is not None:

            # Proportional steering controller
            angular = -self.Kp * error

            # Limit maximum angular velocity
            angular = max(
                -self.max_angular_speed,
                min(self.max_angular_speed, angular)
            )

            move.linear.x = self.linear_speed
            move.angular.z = angular

        else:
            # Stop if road is lost
            move.linear.x = 0.0
            move.angular.z = 0.0

        self.velocity_pub.publish(move)

        # Debugging windows
        cv2.imshow("Road Detection", debug_frame)
        cv2.imshow("Road Mask", mask)

        cv2.waitKey(1)


def main(args=None):

    rclpy.init(args=args)

    node = RoadFollower()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.velocity_pub.publish(Twist())
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
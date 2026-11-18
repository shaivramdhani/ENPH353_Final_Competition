#!/usr/bin/env python3

import rclpy
import cv2
from rclpy.node import Node

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from std_msgs.msg import String

from cv_bridge import CvBridge, CvBridgeError

from controller_pkg.road_detector import detect_road


class CompetitionController(Node):

    def __init__(self):
        super().__init__('competition_controller')

        self.velocity_pub = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        self.score_pub = self.create_publisher(
            String, '/score_tracker', 10
        )

        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.camera_callback,
            1
        )

        self.bridge = CvBridge()

        # Use your registered competition credentials
        self.team = "YOUR_TEAM"
        self.password = "YOUR_PASSWORD"

        # Road-following parameters
        self.Kp = 0.005
        self.linear_speed = 0.15
        self.max_angular_speed = 0.8

        self.road_error = None
        self.last_image_time = None

        # Competition states
        self.state = "READY"
        self.start_time = None

        # Drive for 60 seconds, then stop
        self.drive_duration = 60.0

        self.create_timer(0.1, self.control_loop)

    def publish_score(self, clue_id):
        msg = String()
        msg.data = f"{self.team},{self.password},{clue_id},NA"
        self.score_pub.publish(msg)
        self.get_logger().info(msg.data)

    def camera_callback(self, msg):

        try:
            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='bgr8'
            )

        except CvBridgeError as e:
            self.get_logger().error(str(e))
            return

        # Detect road and generate debug images
        error, debug_frame, mask = detect_road(frame)

        self.road_error = error
        self.last_image_time = self.get_clock().now()

        # Display camera with road centre visualization
        cv2.imshow("Road Detection", debug_frame)

        # Display thresholded image
        cv2.imshow("Road Mask", mask)

        cv2.waitKey(1)

    def control_loop(self):

        if self.state == "READY":

            # Wait for score tracker and camera
            if self.score_pub.get_subscription_count() == 0:
                return

            if self.last_image_time is None:
                return

            self.publish_score(0)
            self.start_time = self.get_clock().now()
            self.state = "DRIVING"

        elif self.state == "DRIVING":

            elapsed = (
                self.get_clock().now() - self.start_time
            ).nanoseconds / 1e9

            if elapsed >= self.drive_duration:
                self.state = "FINISHED"
                self.velocity_pub.publish(Twist())
                return

            cmd = Twist()

            # Only drive if recent camera data is available
            image_age = (
                self.get_clock().now() - self.last_image_time
            ).nanoseconds / 1e9

            if image_age < 0.5 and self.road_error is not None:

                angular = -self.Kp * self.road_error

                angular = max(
                    -self.max_angular_speed,
                    min(self.max_angular_speed, angular)
                )

                cmd.linear.x = self.linear_speed
                cmd.angular.z = angular

            # Otherwise stop until road is detected again
            self.velocity_pub.publish(cmd)

        elif self.state == "FINISHED":

            self.velocity_pub.publish(Twist())
            self.publish_score(-1)
            self.state = "DONE"


def main(args=None):

    rclpy.init(args=args)
    node = CompetitionController()

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
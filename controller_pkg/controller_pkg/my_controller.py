
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

class CompetitionController(Node):

    def __init__(self):
        super().__init__('competition_controller')

        self.velocity_pub = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        self.score_pub = self.create_publisher(
            String, '/score_tracker', 10
        )

        self.team = "SeanShaiv1"
        self.password = "Team1"

        # States: READY, DRIVING, FINISHED
        self.state = "READY"
        self.start_time = None

        # Wait for ROS connections to initialize
        self.create_timer(0.1, self.control_loop)

    def publish_score(self, clue_id):
        msg = String()
        msg.data = (
            f"{self.team},{self.password},{clue_id},NA"
        )
        self.score_pub.publish(msg)
        self.get_logger().info(msg.data)

    def control_loop(self):

        if self.state == "READY":
            # Wait for score tracker to connect
            if self.score_pub.get_subscription_count() == 0:
                return

            self.publish_score(0)
            self.start_time = self.get_clock().now()
            self.state = "DRIVING"

        elif self.state == "DRIVING":

            elapsed = (
                self.get_clock().now() - self.start_time
            ).nanoseconds / 1e9

            cmd = Twist()

            if elapsed < 6.0:
                cmd.linear.x = 0.2
                cmd.angular.z = 0.0
            else:
                self.state = "FINISHED"

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
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
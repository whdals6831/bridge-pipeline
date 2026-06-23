"""로컬 이미지 파일을 ROS 이미지로 반복 발행합니다."""

import sys

import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

from image_capture.parameters import declare_image_parameters
from image_capture.parameters import read_image_parameters


class ImageCaptureNode(Node):
    """이미지 파일 하나를 주기적으로 ROS 이미지로 발행합니다."""

    def __init__(self):
        super().__init__('image_capture')

        declare_image_parameters(self)
        parameters = read_image_parameters(self)
        self.image_path = parameters.image_path
        self.image_topic = parameters.image_topic
        self.frame_id = parameters.frame_id
        self.fps = parameters.fps

        self.bridge = CvBridge()
        self.frame_timer = None
        self.frame = self._load_image()
        self.publisher = self.create_publisher(
            Image,
            self.image_topic,
            qos_profile_sensor_data,
        )
        self.frame_timer = self.create_timer(
            1.0 / self.fps,
            self._publish_frame,
        )

        self.get_logger().info(
            'Publishing %s to %s at %.1f fps'
            % (self.image_path, self.image_topic, self.fps)
        )

    def destroy_node(self):
        """노드를 종료하기 전에 타이머 참조를 정리합니다."""
        self._destroy_frame_timer()
        super().destroy_node()

    def _load_image(self):
        if not self.image_path:
            self.get_logger().error('image_path parameter is required')
            raise RuntimeError('image_path parameter is required')

        frame = cv2.imread(self.image_path, cv2.IMREAD_COLOR)
        if frame is None:
            self.get_logger().error(
                'Failed to read image file: %s' % self.image_path
            )
            raise RuntimeError(
                'Failed to read image file: %s' % self.image_path
            )
        return frame

    def _publish_frame(self):
        message = self.bridge.cv2_to_imgmsg(self.frame, encoding='bgr8')
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self.frame_id
        self.publisher.publish(message)

    def _destroy_frame_timer(self):
        if self.frame_timer is not None:
            self.destroy_timer(self.frame_timer)
            self.frame_timer = None


def main(args=None):
    """이미지 캡처 노드를 시작합니다."""
    rclpy.init(args=args)
    try:
        node = ImageCaptureNode()
    except RuntimeError:
        if rclpy.ok():
            rclpy.shutdown()
        return 1

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        return 0
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""로컬 비디오 파일 프레임을 ROS 이미지로 발행합니다."""

import sys

import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

from video_capture.parameters import declare_video_parameters
from video_capture.parameters import read_video_parameters


DEFAULT_FPS = 30.0


class VideoCaptureNode(Node):
    """OpenCV VideoCapture에서 비디오 프레임을 가져와 발행합니다."""

    def __init__(self):
        super().__init__('video_capture')

        declare_video_parameters(self)
        parameters = read_video_parameters(self)
        self.video_path = parameters.video_path
        self.image_topic = parameters.image_topic
        self.frame_id = parameters.frame_id
        self.requested_fps = parameters.fps
        self.loop = parameters.loop

        self.bridge = CvBridge()
        self.capture = None
        self.frame_timer = None
        self.publisher = self.create_publisher(
            Image,
            self.image_topic,
            qos_profile_sensor_data,
        )

        self._open_capture()

    def destroy_node(self):
        """노드를 종료하기 전에 비디오 캡처를 해제합니다."""
        self._release_capture()
        super().destroy_node()

    def _open_capture(self):
        if not self.video_path:
            self.get_logger().error('video_path parameter is required')
            raise RuntimeError('video_path parameter is required')

        self._release_capture()
        self.capture = cv2.VideoCapture(self.video_path)
        if not self.capture.isOpened():
            self.get_logger().error(
                'Failed to open video file: %s' % self.video_path
            )
            self._release_capture()
            raise RuntimeError(
                'Failed to open video file: %s' % self.video_path
            )

        fps = self._effective_fps()
        self.frame_timer = self.create_timer(1.0 / fps, self._publish_frame)
        self.get_logger().info(
            'Publishing %s to %s at %.1f fps'
            % (self.video_path, self.image_topic, fps)
        )

    def _effective_fps(self):
        if self.requested_fps > 0.0:
            return self.requested_fps

        source_fps = self.capture.get(cv2.CAP_PROP_FPS)
        if source_fps > 0.0:
            return source_fps

        self.get_logger().warn(
            'Video FPS is unavailable; using %.1f' % DEFAULT_FPS
        )
        return DEFAULT_FPS

    def _publish_frame(self):
        if self.capture is None or not self.capture.isOpened():
            self._shutdown_after_error('Video capture is not open')
            return

        success, frame = self.capture.read()
        if not success or frame is None:
            frame = self._read_looped_frame()
            if frame is None:
                return

        message = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self.frame_id
        self.publisher.publish(message)

    def _read_looped_frame(self):
        if not self.loop:
            self.get_logger().info('Reached end of video file')
            self._release_capture()
            self._try_shutdown()
            return None

        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        success, frame = self.capture.read()
        if success and frame is not None:
            return frame

        self._shutdown_after_error(
            'Failed to read frame after looping video file'
        )
        return None

    def _shutdown_after_error(self, message):
        self.get_logger().error(message)
        self._release_capture()
        self._try_shutdown()

    def _try_shutdown(self):
        self.context.try_shutdown()

    def _release_capture(self):
        self._destroy_frame_timer()
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def _destroy_frame_timer(self):
        if self.frame_timer is not None:
            self.destroy_timer(self.frame_timer)
            self.frame_timer = None


def main(args=None):
    """비디오 캡처 노드를 시작합니다."""
    rclpy.init(args=args)
    try:
        node = VideoCaptureNode()
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

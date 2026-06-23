"""로컬에 연결된 카메라 프레임을 ROS 이미지로 발행합니다."""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

from camera_capture.camera_session import CameraSession
from camera_capture.camera_session import CaptureSettings
from camera_capture.parameters import declare_camera_parameters
from camera_capture.parameters import read_camera_parameters


class CameraCaptureNode(Node):
    """카메라 세션을 ROS 노드 생명주기에 연결합니다."""

    def __init__(self):
        super().__init__('camera_capture')

        declare_camera_parameters(self)
        parameters = read_camera_parameters(self)
        settings = CaptureSettings(
            camera_index=parameters.camera_index,
            width=parameters.width,
            height=parameters.height,
            fps=parameters.fps,
            retry_interval_sec=parameters.retry_interval_sec,
            frame_id=parameters.frame_id,
        )

        self.publisher = self.create_publisher(
            Image,
            parameters.image_topic,
            qos_profile_sensor_data,
        )
        self.session = CameraSession(
            settings=settings,
            publisher=self.publisher,
            clock=self.get_clock(),
            logger=self.get_logger(),
            timer_factory=self.create_timer,
            timer_destroyer=self.destroy_timer,
        )

        self.get_logger().info(
            'Publishing camera %d to %s at %dx%d %.1f fps'
            % (
                parameters.camera_index,
                parameters.image_topic,
                parameters.width,
                parameters.height,
                parameters.fps,
            )
        )
        self.session.start()

    def destroy_node(self):
        """노드를 종료하기 전에 카메라 세션을 닫습니다."""
        self.session.close()
        super().destroy_node()


def main(args=None):
    """카메라 캡처 노드를 시작합니다."""
    rclpy.init(args=args)
    node = CameraCaptureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

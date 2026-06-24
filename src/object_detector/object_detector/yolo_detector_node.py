"""카메라 이미지를 구독해 YOLO 객체 탐지 결과를 발행합니다."""

from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D
from vision_msgs.msg import Detection2DArray
from vision_msgs.msg import ObjectHypothesisWithPose

from object_detector.parameters import declare_detector_parameters
from object_detector.parameters import read_detector_parameters
from object_detector.yolo_detector import YoloDetector


class YoloDetectorNode(Node):
    """YOLO 모델로 이미지 프레임의 객체를 탐지합니다."""

    def __init__(self):
        """ROS 파라미터를 읽고 구독/발행 리소스를 생성합니다."""
        super().__init__('yolo_detector')

        declare_detector_parameters(self)
        parameters = read_detector_parameters(self)
        self.input_image_topic = parameters.input_image_topic
        self.detections_topic = parameters.detections_topic
        self.annotated_image_topic = parameters.annotated_image_topic
        self.publish_annotated_image = parameters.publish_annotated_image

        self.bridge = CvBridge()
        self.detector = YoloDetector(
            model_path=parameters.model_path,
            confidence_threshold=parameters.confidence_threshold,
            iou_threshold=parameters.iou_threshold,
            image_size=parameters.image_size,
            device=parameters.device,
        )
        self.logged_effective_device = False
        self.detections_publisher = self.create_publisher(
            Detection2DArray,
            self.detections_topic,
            10,
        )
        self.annotated_image_publisher = None
        if self.publish_annotated_image:
            self.annotated_image_publisher = self.create_publisher(
                Image,
                self.annotated_image_topic,
                qos_profile_sensor_data,
            )
        self.subscription = self.create_subscription(
            Image,
            self.input_image_topic,
            self._image_callback,
            qos_profile_sensor_data,
        )

        self.get_logger().info(
            'Detecting objects from %s with %s on device %s'
            % (
                self.input_image_topic,
                parameters.model_path,
                self.detector.requested_device_name,
            )
        )

    def _image_callback(self, message):
        try:
            frame = self.bridge.imgmsg_to_cv2(
                message,
                desired_encoding='bgr8',
            )
            detections = self.detector.detect(frame)
            detections_message = build_detection_array(
                message.header,
                detections,
            )
            annotated_message = None
            if self.annotated_image_publisher is not None:
                annotated_frame = self.detector.plot_last_result(frame)
                annotated_message = self.bridge.cv2_to_imgmsg(
                    annotated_frame,
                    encoding='bgr8',
                )
                annotated_message.header = message.header
        except Exception as exc:
            self.get_logger().error('Object detection failed: %s' % exc)
            return

        self._log_effective_device_once()
        self.detections_publisher.publish(detections_message)
        if annotated_message is not None:
            self.annotated_image_publisher.publish(annotated_message)

    def _log_effective_device_once(self):
        """첫 추론 후 확인된 YOLO 장치를 한 번만 출력합니다."""
        if self.logged_effective_device:
            return

        effective_device = self.detector.effective_device
        if effective_device is None:
            return

        self.logged_effective_device = True
        self.get_logger().info(
            'YOLO inference is running on device %s' % effective_device
        )


def build_detection_array(header, detections):
    """Build a vision_msgs/Detection2DArray from Detection values."""
    message = Detection2DArray()
    message.header = header
    message.detections = [
        build_detection_message(header, detection)
        for detection in detections
    ]
    return message


def build_detection_message(header, detection):
    """단일 Detection을 vision_msgs/Detection2D로 변환합니다."""
    message = Detection2D()
    message.header = header
    set_bbox_center(message.bbox, detection.center_x, detection.center_y)
    message.bbox.size_x = detection.width
    message.bbox.size_y = detection.height
    message.results = [build_hypothesis(detection)]
    return message


def set_bbox_center(bbox, x_value, y_value):
    """Set BoundingBox2D center across vision_msgs versions."""
    if hasattr(bbox.center, 'position'):
        bbox.center.position.x = x_value
        bbox.center.position.y = y_value
    else:
        bbox.center.x = x_value
        bbox.center.y = y_value
    bbox.center.theta = 0.0


def build_hypothesis(detection):
    """Detection을 vision_msgs/ObjectHypothesisWithPose로 변환합니다."""
    hypothesis = ObjectHypothesisWithPose()
    hypothesis.hypothesis.class_id = detection.label
    hypothesis.hypothesis.score = detection.confidence
    return hypothesis


def main(args=None):
    """YOLO 탐지 노드를 시작합니다."""
    rclpy.init(args=args)
    node = YoloDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

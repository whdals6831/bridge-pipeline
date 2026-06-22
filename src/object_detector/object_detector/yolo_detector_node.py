"""카메라 이미지를 구독해 YOLO 객체 탐지 결과를 발행합니다."""

from dataclasses import dataclass

import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D
from vision_msgs.msg import Detection2DArray
from vision_msgs.msg import ObjectHypothesisWithPose

from object_detector.yolo_detector import YoloDetector


@dataclass(frozen=True)
class DetectionFrameResult:
    """한 프레임 처리 결과입니다."""

    detections_message: Detection2DArray
    annotated_message: Image | None


class DetectionFrameProcessor:
    """ROS 이미지 한 프레임을 탐지 결과 메시지로 변환합니다."""

    def __init__(self, bridge, detector, publish_annotated_image):
        """프레임 처리에 필요한 adapter를 받습니다."""
        self.bridge = bridge
        self.detector = detector
        self.publish_annotated_image = publish_annotated_image

    def process(self, message):
        """이미지 메시지 한 개를 탐지 결과 메시지로 처리합니다."""
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
        if self.publish_annotated_image:
            annotated_frame = draw_detections(frame.copy(), detections)
            annotated_message = self.bridge.cv2_to_imgmsg(
                annotated_frame,
                encoding='bgr8',
            )
            annotated_message.header = message.header

        return DetectionFrameResult(
            detections_message=detections_message,
            annotated_message=annotated_message,
        )


class YoloDetectorNode(Node):
    """YOLO 모델로 이미지 프레임의 객체를 탐지합니다."""

    def __init__(self):
        """ROS 파라미터를 읽고 구독/발행 리소스를 생성합니다."""
        super().__init__('yolo_detector')

        self.declare_parameter('input_image_topic', '/camera/image_raw')
        self.declare_parameter('detections_topic', '/detections')
        self.declare_parameter('annotated_image_topic', '/detections/image')
        self.declare_parameter('model_path', 'yolo11n.pt')
        self.declare_parameter('confidence_threshold', 0.25)
        self.declare_parameter('iou_threshold', 0.7)
        self.declare_parameter('image_size', 640)
        self.declare_parameter('device', '')
        self.declare_parameter('publish_annotated_image', True)

        self.input_image_topic = self._string_parameter('input_image_topic')
        self.detections_topic = self._string_parameter('detections_topic')
        self.annotated_image_topic = self._string_parameter(
            'annotated_image_topic',
        )
        self.publish_annotated_image = self._bool_parameter(
            'publish_annotated_image',
        )

        confidence_threshold = self._bounded_float_parameter(
            'confidence_threshold',
            0.25,
            0.0,
            1.0,
        )
        iou_threshold = self._bounded_float_parameter(
            'iou_threshold',
            0.7,
            0.0,
            1.0,
        )
        image_size = self._positive_int_parameter('image_size', 640)
        model_path = self._string_parameter('model_path')
        device = self._string_parameter('device')

        self.bridge = CvBridge()
        self.detector = YoloDetector(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            image_size=image_size,
            device=device,
        )
        self.frame_processor = DetectionFrameProcessor(
            self.bridge,
            self.detector,
            self.publish_annotated_image,
        )
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
            'Detecting objects from %s with %s'
            % (self.input_image_topic, model_path)
        )

    def _image_callback(self, message):
        try:
            result = self.frame_processor.process(message)
        except Exception as exc:
            self.get_logger().error('Object detection failed: %s' % exc)
            return

        self.detections_publisher.publish(result.detections_message)
        if (
            self.annotated_image_publisher is not None and
            result.annotated_message is not None
        ):
            self.annotated_image_publisher.publish(result.annotated_message)

    def _string_parameter(self, name):
        return self.get_parameter(name).get_parameter_value().string_value

    def _bool_parameter(self, name):
        return self.get_parameter(name).get_parameter_value().bool_value

    def _bounded_float_parameter(
        self,
        name,
        default_value,
        minimum,
        maximum,
    ):
        value = self.get_parameter(name).get_parameter_value().double_value
        if minimum <= value <= maximum:
            return value
        self.get_logger().warn(
            '%s must be between %.1f and %.1f; using %.2f'
            % (name, minimum, maximum, default_value)
        )
        return default_value

    def _positive_int_parameter(self, name, default_value):
        value = self.get_parameter(name).get_parameter_value().integer_value
        if value > 0:
            return value
        self.get_logger().warn(
            '%s must be positive; using %d' % (name, default_value)
        )
        return default_value


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


def draw_detections(frame, detections):
    """프레임에 탐지 박스와 레이블을 그립니다."""
    for detection in detections:
        start = (int(detection.x_min), int(detection.y_min))
        end = (int(detection.x_max), int(detection.y_max))
        label = '%s %.2f' % (detection.label, detection.confidence)
        cv2.rectangle(frame, start, end, (0, 255, 0), 2)
        cv2.putText(
            frame,
            label,
            (start[0], max(start[1] - 6, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
    return frame


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
        rclpy.shutdown()


if __name__ == '__main__':
    main()

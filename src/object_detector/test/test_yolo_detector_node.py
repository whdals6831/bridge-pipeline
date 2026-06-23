"""YOLO 탐지 ROS 메시지 변환 테스트입니다."""

import numpy as np
from sensor_msgs.msg import Image
from std_msgs.msg import Header

from object_detector.yolo_detector import Detection
from object_detector.yolo_detector_node import build_detection_array
from object_detector.yolo_detector_node import YoloDetectorNode


def make_detection():
    return Detection(
        class_id=1,
        label='person',
        confidence=0.9,
        x_min=10.0,
        y_min=20.0,
        x_max=50.0,
        y_max=80.0,
    )


class FakeBridge:
    """테스트용 CvBridge 대역입니다."""

    def __init__(self, frame):
        self.frame = frame
        self.imgmsg_encoding = None
        self.cv2_encoding = None
        self.annotated_frame = None

    def imgmsg_to_cv2(self, message, desired_encoding):
        self.imgmsg_encoding = desired_encoding
        return self.frame

    def cv2_to_imgmsg(self, frame, encoding):
        self.cv2_encoding = encoding
        self.annotated_frame = frame
        return Image()


class FakeDetector:
    """테스트용 detector adapter입니다."""

    def __init__(self, detections, effective_device=None):
        self.detections = detections
        self.effective_device = effective_device
        self.detected_frame = None

    def detect(self, frame):
        self.detected_frame = frame
        return self.detections


class FakeLogger:
    """테스트용 ROS logger 대역입니다."""

    def __init__(self):
        self.info_messages = []

    def info(self, message):
        self.info_messages.append(message)


def test_build_detection_array_sets_bbox_and_hypothesis():
    header = Header()
    header.frame_id = 'camera_frame'
    detection = make_detection()

    message = build_detection_array(header, [detection])

    assert message.header.frame_id == 'camera_frame'
    assert len(message.detections) == 1
    detection_message = message.detections[0]
    assert detection_message.bbox.center.position.x == 30.0
    assert detection_message.bbox.center.position.y == 50.0
    assert detection_message.bbox.size_x == 40.0
    assert detection_message.bbox.size_y == 60.0
    assert detection_message.results[0].hypothesis.class_id == 'person'
    assert detection_message.results[0].hypothesis.score == 0.9


def make_node(frame, detections, publish_annotated_image=True):
    node = object.__new__(YoloDetectorNode)
    node.bridge = FakeBridge(frame)
    node.detector = FakeDetector(detections)
    node.logged_effective_device = True
    node.detections_publisher = FakePublisher()
    node.annotated_image_publisher = (
        FakePublisher() if publish_annotated_image else None
    )
    node.get_logger = lambda: FakeLogger()
    return node


class FakePublisher:
    """발행된 메시지를 기록합니다."""

    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


def test_image_callback_builds_detection_and_annotation_messages():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    node = make_node(frame, [make_detection()])
    image_message = Image()
    image_message.header.frame_id = 'camera_frame'

    node._image_callback(image_message)

    assert node.bridge.imgmsg_encoding == 'bgr8'
    assert node.bridge.cv2_encoding == 'bgr8'
    assert node.detector.detected_frame is frame
    detections_message = node.detections_publisher.messages[0]
    assert detections_message.header.frame_id == 'camera_frame'
    assert len(detections_message.detections) == 1
    annotated_message = node.annotated_image_publisher.messages[0]
    assert annotated_message.header.frame_id == 'camera_frame'
    assert node.bridge.annotated_frame is not frame


def test_image_callback_can_skip_annotation_message():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    node = make_node(frame, [make_detection()], publish_annotated_image=False)
    image_message = Image()

    node._image_callback(image_message)

    assert len(node.detections_publisher.messages) == 1
    assert node.bridge.cv2_encoding is None


def test_log_effective_device_once_logs_first_available_device():
    node = object.__new__(YoloDetectorNode)
    node.detector = FakeDetector([], effective_device='cuda:0')
    node.logged_effective_device = False
    logger = FakeLogger()
    node.get_logger = lambda: logger

    node._log_effective_device_once()
    node._log_effective_device_once()

    assert logger.info_messages == [
        'YOLO inference is running on device cuda:0',
    ]

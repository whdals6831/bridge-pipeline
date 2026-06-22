"""YOLO 탐지 ROS 메시지 변환 테스트입니다."""

import numpy as np
from sensor_msgs.msg import Image
from std_msgs.msg import Header

from object_detector.yolo_detector import Detection
from object_detector.yolo_detector_node import build_detection_array
from object_detector.yolo_detector_node import DetectionFrameProcessor


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

    def __init__(self, detections):
        self.detections = detections
        self.detected_frame = None

    def detect(self, frame):
        self.detected_frame = frame
        return self.detections


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


def test_detection_frame_processor_builds_detection_and_annotation_messages():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    bridge = FakeBridge(frame)
    detector = FakeDetector([make_detection()])
    processor = DetectionFrameProcessor(
        bridge,
        detector,
        publish_annotated_image=True,
    )
    image_message = Image()
    image_message.header.frame_id = 'camera_frame'

    result = processor.process(image_message)

    assert bridge.imgmsg_encoding == 'bgr8'
    assert bridge.cv2_encoding == 'bgr8'
    assert detector.detected_frame is frame
    assert result.detections_message.header.frame_id == 'camera_frame'
    assert len(result.detections_message.detections) == 1
    assert result.annotated_message.header.frame_id == 'camera_frame'
    assert bridge.annotated_frame is not frame


def test_detection_frame_processor_can_skip_annotation_message():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    bridge = FakeBridge(frame)
    detector = FakeDetector([make_detection()])
    processor = DetectionFrameProcessor(
        bridge,
        detector,
        publish_annotated_image=False,
    )
    image_message = Image()

    result = processor.process(image_message)

    assert result.annotated_message is None
    assert bridge.cv2_encoding is None

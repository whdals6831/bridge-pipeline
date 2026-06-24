"""YOLO 탐지 변환 유틸리티 테스트입니다."""

import numpy as np

from object_detector.yolo_detector import Detection
from object_detector.yolo_detector import detection_iou
from object_detector.yolo_detector import detections_from_ultralytics_result
from object_detector.yolo_detector import suppress_duplicate_detections
from object_detector.yolo_detector import YoloDetector
from object_detector.yolo_detector import _device_name


class Boxes:
    """테스트용 Ultralytics boxes 대역입니다."""

    xyxy = [[10.0, 20.0, 50.0, 80.0]]
    conf = [0.75]
    cls = [1.0]


class Result:
    """테스트용 Ultralytics result 대역입니다."""

    boxes = Boxes()
    names = {1: 'person'}


def test_detections_from_ultralytics_result():
    detections = detections_from_ultralytics_result(Result())

    assert len(detections) == 1
    detection = detections[0]
    assert detection.class_id == 1
    assert detection.label == 'person'
    assert detection.confidence == 0.75
    assert detection.center_x == 30.0
    assert detection.center_y == 50.0
    assert detection.width == 40.0
    assert detection.height == 60.0


def make_detection(label, confidence, x_min, y_min, x_max, y_max):
    return Detection(
        class_id=0,
        label=label,
        confidence=confidence,
        x_min=x_min,
        y_min=y_min,
        x_max=x_max,
        y_max=y_max,
    )


def test_detection_iou_returns_overlap_ratio():
    first = make_detection('person', 0.9, 0.0, 0.0, 10.0, 10.0)
    second = make_detection('person', 0.8, 5.0, 0.0, 15.0, 10.0)

    assert detection_iou(first, second) == 0.3333333333333333


def test_suppress_duplicate_detections_keeps_highest_confidence_same_label():
    lower_confidence = make_detection('person', 0.6, 0.0, 0.0, 10.0, 10.0)
    higher_confidence = make_detection('person', 0.9, 1.0, 1.0, 11.0, 11.0)

    detections = suppress_duplicate_detections(
        [lower_confidence, higher_confidence],
        iou_threshold=0.5,
    )

    assert detections == [higher_confidence]


def test_suppress_duplicate_detections_ignores_label_case():
    lower_confidence = make_detection('Person', 0.6, 0.0, 0.0, 10.0, 10.0)
    higher_confidence = make_detection('person', 0.9, 1.0, 1.0, 11.0, 11.0)

    detections = suppress_duplicate_detections(
        [lower_confidence, higher_confidence],
        iou_threshold=0.5,
    )

    assert detections == [higher_confidence]


def test_suppress_duplicate_detections_keeps_overlapping_different_labels():
    person = make_detection('person', 0.9, 0.0, 0.0, 10.0, 10.0)
    mannequin = make_detection('mannequin', 0.8, 1.0, 1.0, 11.0, 11.0)

    detections = suppress_duplicate_detections(
        [person, mannequin],
        iou_threshold=0.5,
    )

    assert detections == [person, mannequin]


class PlotResult:
    """plot 호출을 기록하는 Ultralytics result 대역입니다."""

    def __init__(self):
        self.plot_kwargs = None

    def plot(self, **kwargs):
        self.plot_kwargs = kwargs
        return kwargs['img']


def test_plot_last_result_uses_ultralytics_class_colors():
    detector = object.__new__(YoloDetector)
    detector.last_result = PlotResult()
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    annotated = detector.plot_last_result(frame)

    assert annotated is not frame
    assert detector.last_result.plot_kwargs['color_mode'] == 'class'
    assert detector.last_result.plot_kwargs['txt_color'] == (255, 255, 255)


def test_plot_last_result_copies_frame_without_result():
    detector = object.__new__(YoloDetector)
    detector.last_result = None
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    annotated = detector.plot_last_result(frame)

    assert annotated is not frame
    assert np.array_equal(annotated, frame)


class ModelWithDevice:
    """device 속성이 있는 YOLO 모델 대역입니다."""

    device = 'cuda:0'


class Parameter:
    """PyTorch parameter 대역입니다."""

    device = 'cpu'


class TorchModel:
    """parameters로 장치를 노출하는 torch 모델 대역입니다."""

    def parameters(self):
        return iter([Parameter()])


class YoloModel:
    """내부 torch 모델을 가진 YOLO 모델 대역입니다."""

    model = TorchModel()


def test_device_name_reads_yolo_model_device():
    assert _device_name(ModelWithDevice()) == 'cuda:0'


def test_device_name_falls_back_to_torch_parameter_device():
    assert _device_name(YoloModel()) == 'cpu'

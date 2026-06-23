"""YOLO 탐지 변환 유틸리티 테스트입니다."""

from object_detector.yolo_detector import detections_from_ultralytics_result
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

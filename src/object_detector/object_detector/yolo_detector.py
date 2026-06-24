"""YOLO 모델 출력을 패키지 내부 탐지 표현으로 변환합니다."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    """단일 객체 탐지 결과입니다."""

    class_id: int
    label: str
    confidence: float
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self):
        """탐지 박스 너비를 반환합니다."""
        return self.x_max - self.x_min

    @property
    def height(self):
        """탐지 박스 높이를 반환합니다."""
        return self.y_max - self.y_min

    @property
    def center_x(self):
        """탐지 박스 중심 x 좌표를 반환합니다."""
        return self.x_min + self.width / 2.0

    @property
    def center_y(self):
        """탐지 박스 중심 y 좌표를 반환합니다."""
        return self.y_min + self.height / 2.0


class YoloDetector:
    """Ultralytics YOLO 모델을 사용해 OpenCV 프레임을 탐지합니다."""

    def __init__(
        self,
        model_path,
        confidence_threshold=0.25,
        iou_threshold=0.7,
        image_size=640,
        device='',
    ):
        """YOLO 모델을 로드합니다."""
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                'ultralytics package is required. Install it with '
                '`pip install ultralytics` in the ROS environment.'
            ) from exc

        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.image_size = image_size
        self.device = device or None
        self.effective_device = None
        self.last_result = None

    def detect(self, frame):
        """프레임에서 객체를 탐지합니다."""
        self.last_result = None
        results = self.model.predict(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.image_size,
            device=self.device,
            verbose=False,
        )
        self.effective_device = _device_name(self.model)
        if not results:
            return []
        self.last_result = results[0]
        return detections_from_ultralytics_result(self.last_result)

    def plot_last_result(self, frame):
        """마지막 YOLO 결과를 Ultralytics 기본 스타일로 그립니다."""
        if self.last_result is None:
            return frame.copy()
        return self.last_result.plot(
            img=frame.copy(),
            color_mode='class',
            txt_color=(255, 255, 255),
        )

    @property
    def requested_device_name(self):
        """요청된 추론 장치 이름을 반환합니다."""
        return self.device or 'auto'


def detections_from_ultralytics_result(result):
    """Ultralytics Results 객체를 Detection 목록으로 변환합니다."""
    boxes = getattr(result, 'boxes', None)
    if boxes is None:
        return []

    xyxy_values = _to_list(getattr(boxes, 'xyxy', []))
    confidence_values = _to_list(getattr(boxes, 'conf', []))
    class_values = _to_list(getattr(boxes, 'cls', []))
    names = getattr(result, 'names', {}) or {}

    detections = []
    for xyxy, confidence, class_id in zip(
        xyxy_values,
        confidence_values,
        class_values,
    ):
        class_id = int(class_id)
        detections.append(Detection(
            class_id=class_id,
            label=str(names.get(class_id, class_id)),
            confidence=float(confidence),
            x_min=float(xyxy[0]),
            y_min=float(xyxy[1]),
            x_max=float(xyxy[2]),
            y_max=float(xyxy[3]),
        ))
    return detections


def _to_list(value):
    if hasattr(value, 'cpu'):
        value = value.cpu()
    if hasattr(value, 'numpy'):
        value = value.numpy()
    if hasattr(value, 'tolist'):
        return value.tolist()
    return list(value)


def _device_name(model):
    device = getattr(model, 'device', None)
    if device is not None:
        return str(device)

    torch_model = getattr(model, 'model', None)
    device = getattr(torch_model, 'device', None)
    if device is not None:
        return str(device)

    parameters = getattr(torch_model, 'parameters', None)
    if parameters is None:
        return None
    try:
        first_parameter = next(parameters())
    except (StopIteration, TypeError):
        return None
    device = getattr(first_parameter, 'device', None)
    if device is None:
        return None
    return str(device)

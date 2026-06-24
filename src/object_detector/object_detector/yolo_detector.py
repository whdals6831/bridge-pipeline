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


class MultiYoloDetector:
    """여러 YOLO 모델 결과를 병합해 중복 탐지를 제거합니다."""

    def __init__(
        self,
        model_paths,
        confidence_threshold=0.25,
        iou_threshold=0.7,
        duplicate_iou_threshold=0.7,
        image_size=640,
        device='',
    ):
        """YOLO 모델 목록을 로드합니다."""
        if not model_paths:
            raise ValueError('model_paths must contain at least one path')

        self.detectors = [
            YoloDetector(
                model_path=model_path,
                confidence_threshold=confidence_threshold,
                iou_threshold=iou_threshold,
                image_size=image_size,
                device=device,
            )
            for model_path in model_paths
        ]
        self.duplicate_iou_threshold = duplicate_iou_threshold

    def detect(self, frame):
        """모든 모델로 추론한 뒤 같은 label 중복 박스를 제거합니다."""
        detections = []
        for detector in self.detectors:
            detections.extend(detector.detect(frame))
        return suppress_duplicate_detections(
            detections,
            self.duplicate_iou_threshold,
        )

    def plot_detections(self, frame, detections):
        """병합된 Detection 목록을 OpenCV 이미지에 그립니다."""
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError(
                'OpenCV is required to publish annotated images.'
            ) from exc

        annotated = frame.copy()
        for detection in detections:
            x_min = int(round(detection.x_min))
            y_min = int(round(detection.y_min))
            x_max = int(round(detection.x_max))
            y_max = int(round(detection.y_max))
            color = _label_color(detection.label)
            cv2.rectangle(
                annotated,
                (x_min, y_min),
                (x_max, y_max),
                color,
                2,
            )
            text = '%s %.2f' % (detection.label, detection.confidence)
            _draw_label(cv2, annotated, text, x_min, y_min, color)
        return annotated

    @property
    def effective_device(self):
        """첫 모델에서 확인된 추론 장치 이름을 반환합니다."""
        for detector in self.detectors:
            if detector.effective_device is not None:
                return detector.effective_device
        return None

    @property
    def requested_device_name(self):
        """요청된 추론 장치 이름을 반환합니다."""
        return self.detectors[0].requested_device_name


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


def suppress_duplicate_detections(detections, iou_threshold):
    """같은 label끼리 IoU가 높은 중복 박스를 confidence 기준으로 제거합니다."""
    kept = []
    sorted_detections = sorted(
        detections,
        key=lambda detection: detection.confidence,
        reverse=True,
    )
    for detection in sorted_detections:
        has_duplicate = any(
            _label_key(detection.label) == _label_key(kept_detection.label)
            and detection_iou(detection, kept_detection) >= iou_threshold
            for kept_detection in kept
        )
        if not has_duplicate:
            kept.append(detection)
    return kept


def _label_key(label):
    return label.casefold()


def detection_iou(first, second):
    """두 Detection 박스의 IoU를 반환합니다."""
    intersection_x_min = max(first.x_min, second.x_min)
    intersection_y_min = max(first.y_min, second.y_min)
    intersection_x_max = min(first.x_max, second.x_max)
    intersection_y_max = min(first.y_max, second.y_max)
    intersection_width = max(0.0, intersection_x_max - intersection_x_min)
    intersection_height = max(0.0, intersection_y_max - intersection_y_min)
    intersection_area = intersection_width * intersection_height

    first_area = max(0.0, first.width) * max(0.0, first.height)
    second_area = max(0.0, second.width) * max(0.0, second.height)
    union_area = first_area + second_area - intersection_area
    if union_area <= 0.0:
        return 0.0
    return intersection_area / union_area


def _label_color(label):
    value = sum((index + 1) * ord(char) for index, char in enumerate(label))
    return (
        64 + value % 160,
        64 + (value // 3) % 160,
        64 + (value // 7) % 160,
    )


def _draw_label(cv2, image, text, x_min, y_min, color):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    text_size, baseline = cv2.getTextSize(
        text,
        font,
        font_scale,
        thickness,
    )
    text_width, text_height = text_size
    label_y_min = max(0, y_min - text_height - baseline - 4)
    label_y_max = label_y_min + text_height + baseline + 4
    label_x_max = x_min + text_width + 6
    cv2.rectangle(
        image,
        (x_min, label_y_min),
        (label_x_max, label_y_max),
        color,
        -1,
    )
    cv2.putText(
        image,
        text,
        (x_min + 3, label_y_max - baseline - 2),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


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

"""객체 탐지 런타임 파라미터 계약입니다."""

from dataclasses import dataclass
from dataclasses import replace


@dataclass(frozen=True)
class ParameterSpec:
    """객체 탐지 런타임이 노출하는 ROS 파라미터입니다."""

    name: str
    default: object
    value_type: type | None = None

    @property
    def launch_default(self):
        """런치 인자 기본값을 문자열로 반환합니다."""
        if isinstance(self.default, bool):
            return str(self.default).lower()
        return str(self.default)


@dataclass(frozen=True)
class DetectorParameters:
    """검증된 YOLO 객체 탐지 파라미터입니다."""

    input_image_topic: str
    detections_topic: str
    annotated_image_topic: str
    model_paths: str
    confidence_threshold: float
    iou_threshold: float
    duplicate_iou_threshold: float
    image_size: int
    device: str
    publish_annotated_image: bool


PARAMETER_SPECS = (
    ParameterSpec('input_image_topic', '/camera/image_raw'),
    ParameterSpec('detections_topic', '/detections'),
    ParameterSpec('annotated_image_topic', '/detections/image'),
    ParameterSpec('model_paths', 'yolo11n.pt'),
    ParameterSpec('confidence_threshold', 0.25, float),
    ParameterSpec('iou_threshold', 0.7, float),
    ParameterSpec('duplicate_iou_threshold', 0.7, float),
    ParameterSpec('image_size', 640, int),
    ParameterSpec('device', ''),
    ParameterSpec('publish_annotated_image', True, bool),
)


def declare_detector_parameters(node):
    """ROS 노드에 탐지 파라미터를 선언합니다."""
    for spec in PARAMETER_SPECS:
        node.declare_parameter(spec.name, spec.default)


def read_detector_parameters(node):
    """ROS 노드에서 탐지 파라미터를 읽고 검증합니다."""
    parameters = DetectorParameters(
        input_image_topic=_string_parameter(node, 'input_image_topic'),
        detections_topic=_string_parameter(node, 'detections_topic'),
        annotated_image_topic=_string_parameter(
            node,
            'annotated_image_topic',
        ),
        model_paths=_string_parameter(node, 'model_paths'),
        confidence_threshold=_double_parameter(
            node,
            'confidence_threshold',
        ),
        iou_threshold=_double_parameter(node, 'iou_threshold'),
        duplicate_iou_threshold=_double_parameter(
            node,
            'duplicate_iou_threshold',
        ),
        image_size=_integer_parameter(node, 'image_size'),
        device=_string_parameter(node, 'device'),
        publish_annotated_image=_bool_parameter(
            node,
            'publish_annotated_image',
        ),
    )
    return validate_detector_parameters(parameters, node.get_logger().warn)


def validate_detector_parameters(parameters, warn):
    """탐지 파라미터를 검증하고 보정된 값을 반환합니다."""
    parameters = _bounded_float_parameter(
        parameters,
        warn,
        name='confidence_threshold',
        default_value=0.25,
        minimum=0.0,
        maximum=1.0,
    )
    parameters = _bounded_float_parameter(
        parameters,
        warn,
        name='iou_threshold',
        default_value=0.7,
        minimum=0.0,
        maximum=1.0,
    )
    parameters = _bounded_float_parameter(
        parameters,
        warn,
        name='duplicate_iou_threshold',
        default_value=0.7,
        minimum=0.0,
        maximum=1.0,
    )
    if parameters.image_size <= 0:
        warn('image_size must be positive; using 640')
        parameters = replace(parameters, image_size=640)
    if not parse_model_paths(parameters.model_paths):
        warn('model_paths must contain at least one path; using yolo11n.pt')
        parameters = replace(parameters, model_paths='yolo11n.pt')
    return parameters


def parse_model_paths(value):
    """콤마 구분 모델 경로 문자열을 정리된 경로 목록으로 변환합니다."""
    return [
        path.strip()
        for path in value.split(',')
        if path.strip()
    ]


def _bounded_float_parameter(
    parameters,
    warn,
    name,
    default_value,
    minimum,
    maximum,
):
    value = getattr(parameters, name)
    if minimum <= value <= maximum:
        return parameters
    warn(
        '%s must be between %.1f and %.1f; using %.2f'
        % (name, minimum, maximum, default_value)
    )
    return replace(parameters, **{name: default_value})


def _integer_parameter(node, name):
    return node.get_parameter(name).get_parameter_value().integer_value


def _double_parameter(node, name):
    return node.get_parameter(name).get_parameter_value().double_value


def _string_parameter(node, name):
    return node.get_parameter(name).get_parameter_value().string_value


def _bool_parameter(node, name):
    return node.get_parameter(name).get_parameter_value().bool_value

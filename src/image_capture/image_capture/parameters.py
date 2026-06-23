"""이미지 캡처 런타임 파라미터 계약입니다."""

from dataclasses import dataclass
from dataclasses import replace


@dataclass(frozen=True)
class ParameterSpec:
    """이미지 캡처 런타임이 노출하는 ROS 파라미터입니다."""

    name: str
    default: object
    value_type: type | None = None

    @property
    def launch_default(self):
        """런치 인자 기본값을 문자열로 반환합니다."""
        return str(self.default)


@dataclass(frozen=True)
class ImageParameters:
    """검증된 이미지 캡처 파라미터입니다."""

    image_path: str
    image_topic: str
    frame_id: str
    fps: float


PARAMETER_SPECS = (
    ParameterSpec('image_path', ''),
    ParameterSpec('image_topic', '/image/image_raw'),
    ParameterSpec('frame_id', 'image_frame'),
    ParameterSpec('fps', 1.0, float),
)


def declare_image_parameters(node):
    """ROS 노드에 이미지 캡처 파라미터를 선언합니다."""
    for spec in PARAMETER_SPECS:
        node.declare_parameter(spec.name, spec.default)


def read_image_parameters(node):
    """ROS 노드에서 이미지 캡처 파라미터를 읽고 검증합니다."""
    parameters = ImageParameters(
        image_path=_string_parameter(node, 'image_path'),
        image_topic=_string_parameter(node, 'image_topic'),
        frame_id=_string_parameter(node, 'frame_id'),
        fps=_double_parameter(node, 'fps'),
    )
    return validate_image_parameters(parameters, node.get_logger().warn)


def validate_image_parameters(parameters, warn):
    """이미지 캡처 파라미터를 검증하고 보정된 값을 반환합니다."""
    if parameters.fps <= 0.0:
        warn('fps must be positive; using 1.0')
        parameters = replace(parameters, fps=1.0)
    return parameters


def _double_parameter(node, name):
    return node.get_parameter(name).get_parameter_value().double_value


def _string_parameter(node, name):
    return node.get_parameter(name).get_parameter_value().string_value

"""모니터링 fusion 파라미터 계약입니다."""

from dataclasses import dataclass
from dataclasses import replace


@dataclass(frozen=True)
class ParameterSpec:
    """모니터링 fusion 노드가 노출하는 ROS 파라미터입니다."""

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
class FusionParameters:
    """검증된 모니터링 fusion 파라미터입니다."""

    roi_alarm_topic: str
    detections_topic: str
    output_topic: str
    max_age_seconds: float
    required_detection_labels: str


PARAMETER_SPECS = (
    ParameterSpec('roi_alarm_topic', '/lidar/roi_alarm'),
    ParameterSpec('detections_topic', '/detections'),
    ParameterSpec('output_topic', '/monitoring/alarms'),
    ParameterSpec('max_age_seconds', 0.3, float),
    ParameterSpec('required_detection_labels', 'person,car,truck'),
)


def declare_fusion_parameters(node):
    """ROS 노드에 fusion 파라미터를 선언합니다."""
    for spec in PARAMETER_SPECS:
        node.declare_parameter(spec.name, spec.default)


def read_fusion_parameters(node):
    """ROS 노드에서 fusion 파라미터를 읽고 검증합니다."""
    parameters = FusionParameters(
        roi_alarm_topic=_string_parameter(node, 'roi_alarm_topic'),
        detections_topic=_string_parameter(node, 'detections_topic'),
        output_topic=_string_parameter(node, 'output_topic'),
        max_age_seconds=_double_parameter(node, 'max_age_seconds'),
        required_detection_labels=_string_parameter(
            node,
            'required_detection_labels',
        ),
    )
    return validate_fusion_parameters(parameters, node.get_logger().warn)


def validate_fusion_parameters(parameters, warn):
    """Fusion 파라미터를 검증하고 보정된 값을 반환합니다."""
    if parameters.max_age_seconds <= 0.0:
        warn('max_age_seconds must be positive; using 0.3')
        parameters = replace(parameters, max_age_seconds=0.3)
    return parameters


def parse_required_labels(value):
    """콤마 구분 label 문자열을 비교용 소문자 집합으로 변환합니다."""
    return {
        label.strip().lower()
        for label in value.split(',')
        if label.strip()
    }


def _double_parameter(node, name):
    return node.get_parameter(name).get_parameter_value().double_value


def _string_parameter(node, name):
    return node.get_parameter(name).get_parameter_value().string_value

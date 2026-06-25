"""모니터링 fusion 파라미터 계약 테스트입니다."""

from monitoring_fusion.parameters import FusionParameters
from monitoring_fusion.parameters import PARAMETER_SPECS
from monitoring_fusion.parameters import parse_required_labels
from monitoring_fusion.parameters import validate_fusion_parameters


def test_parameter_specs_keep_runtime_defaults():
    specs = {spec.name: spec for spec in PARAMETER_SPECS}

    assert specs['roi_alarm_topic'].default == '/lidar/roi_alarm'
    assert specs['detections_topic'].default == '/detections'
    assert specs['output_topic'].default == '/monitoring/alarms'
    assert specs['max_age_seconds'].default == 0.3
    assert specs['required_detection_labels'].default == 'person,car,truck'
    assert specs['max_age_seconds'].value_type is float


def test_validate_fusion_parameters_corrects_invalid_values():
    warnings = []
    parameters = FusionParameters(
        roi_alarm_topic='/lidar/roi_alarm',
        detections_topic='/detections',
        output_topic='/monitoring/alarms',
        max_age_seconds=0.0,
        required_detection_labels='person',
    )

    validated = validate_fusion_parameters(parameters, warnings.append)

    assert validated.max_age_seconds == 0.3
    assert warnings == ['max_age_seconds must be positive; using 0.3']


def test_parse_required_labels_splits_and_normalizes_labels():
    assert parse_required_labels('Person, car,, BUS ') == {
        'person',
        'car',
        'bus',
    }

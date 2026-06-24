"""객체 탐지 파라미터 계약 테스트입니다."""

from object_detector.parameters import DetectorParameters
from object_detector.parameters import PARAMETER_SPECS
from object_detector.parameters import parse_model_paths
from object_detector.parameters import validate_detector_parameters


def test_parameter_specs_keep_runtime_defaults():
    specs = {spec.name: spec for spec in PARAMETER_SPECS}

    assert specs['input_image_topic'].default == '/camera/image_raw'
    assert specs['detections_topic'].default == '/detections'
    assert specs['annotated_image_topic'].default == '/detections/image'
    assert specs['model_paths'].default == 'yolo11n.pt'
    assert specs['confidence_threshold'].default == 0.25
    assert specs['iou_threshold'].default == 0.7
    assert specs['duplicate_iou_threshold'].default == 0.7
    assert specs['image_size'].default == 640
    assert specs['device'].default == ''
    assert specs['publish_annotated_image'].default is True
    assert specs['publish_annotated_image'].launch_default == 'true'
    assert specs['confidence_threshold'].value_type is float
    assert specs['publish_annotated_image'].value_type is bool


def test_validate_detector_parameters_corrects_invalid_values():
    warnings = []
    parameters = DetectorParameters(
        input_image_topic='/camera/image_raw',
        detections_topic='/detections',
        annotated_image_topic='/detections/image',
        model_paths='',
        confidence_threshold=-0.1,
        iou_threshold=1.1,
        duplicate_iou_threshold=1.1,
        image_size=0,
        device='',
        publish_annotated_image=True,
    )

    validated = validate_detector_parameters(parameters, warnings.append)

    assert validated.confidence_threshold == 0.25
    assert validated.iou_threshold == 0.7
    assert validated.duplicate_iou_threshold == 0.7
    assert validated.image_size == 640
    assert validated.model_paths == 'yolo11n.pt'
    assert warnings == [
        'confidence_threshold must be between 0.0 and 1.0; using 0.25',
        'iou_threshold must be between 0.0 and 1.0; using 0.70',
        'duplicate_iou_threshold must be between 0.0 and 1.0; using 0.70',
        'image_size must be positive; using 640',
        'model_paths must contain at least one path; using yolo11n.pt',
    ]


def test_parse_model_paths_splits_comma_separated_paths():
    assert parse_model_paths('yolo11n.pt, /tmp/custom.pt,,best.pt ') == [
        'yolo11n.pt',
        '/tmp/custom.pt',
        'best.pt',
    ]

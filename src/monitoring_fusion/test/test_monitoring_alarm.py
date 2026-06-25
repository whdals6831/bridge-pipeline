"""모니터링 알람 조합 테스트입니다."""

import json
from types import SimpleNamespace

from monitoring_fusion.monitoring_alarm import build_monitoring_event
from monitoring_fusion.monitoring_alarm import encode_monitoring_event


def stamp(sec, nanosec=0):
    return SimpleNamespace(sec=sec, nanosec=nanosec)


def header(sec, nanosec=0):
    return SimpleNamespace(stamp=stamp(sec, nanosec))


def roi_alarm(name, alarm=True, point_count=70, threshold=50):
    return SimpleNamespace(
        name=name,
        alarm=alarm,
        point_count=point_count,
        threshold=threshold,
    )


def detection(label='person', score=0.9):
    hypothesis = SimpleNamespace(class_id=label, score=score)
    result = SimpleNamespace(hypothesis=hypothesis)
    center = SimpleNamespace(position=SimpleNamespace(x=10.0, y=20.0))
    bbox = SimpleNamespace(center=center, size_x=30.0, size_y=40.0)
    return SimpleNamespace(results=[result], bbox=bbox)


def roi_message(sec=10, alarms=None):
    return SimpleNamespace(
        header=header(sec),
        alarms=alarms if alarms is not None else [roi_alarm('front')],
    )


def detections_message(sec=10, detections=None):
    return SimpleNamespace(
        header=header(sec),
        detections=(
            detections if detections is not None else [detection('person')]
        ),
    )


def test_build_monitoring_event_marks_red_for_danger_zone_and_risk_label():
    event = build_monitoring_event(
        roi_message(alarms=[roi_alarm('danger_zone')]),
        detections_message(),
        max_age_seconds=0.3,
        required_labels={'person', 'car', 'truck'},
    )

    assert event['alarm'] is True
    assert event['level'] == 'red'
    assert event['status'] == 'red'
    assert event['active_rois'][0]['name'] == 'danger_zone'
    assert event['matched_detections'][0]['label'] == 'person'


def test_build_monitoring_event_marks_stale_active_roi_as_yellow_alarm():
    event = build_monitoring_event(
        roi_message(sec=10, alarms=[roi_alarm('danger_zone')]),
        detections_message(sec=11),
        max_age_seconds=0.3,
        required_labels={'person', 'car', 'truck'},
    )

    assert event['alarm'] is True
    assert event['level'] == 'yellow'
    assert event['status'] == 'stale'
    assert event['matched_detections'] == []


def test_build_monitoring_event_marks_non_matching_alarm_as_yellow():
    event = build_monitoring_event(
        roi_message(alarms=[roi_alarm('danger_zone')]),
        detections_message(detections=[detection('car')]),
        max_age_seconds=0.3,
        required_labels={'person'},
    )

    assert event['alarm'] is True
    assert event['level'] == 'yellow'
    assert event['status'] == 'yellow'


def test_build_monitoring_event_marks_no_roi_alarm_as_green():
    event = build_monitoring_event(
        roi_message(alarms=[roi_alarm('danger_zone', alarm=False)]),
        detections_message(),
        max_age_seconds=0.3,
        required_labels={'person', 'car', 'truck'},
    )

    assert event['alarm'] is False
    assert event['level'] == 'green'
    assert event['status'] == 'green'


def test_encode_monitoring_event_returns_json_string():
    encoded = encode_monitoring_event({'alarm': True, 'status': 'active'})

    assert json.loads(encoded) == {'alarm': True, 'status': 'active'}

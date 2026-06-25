"""라이다 ROI 알람과 객체 검출을 최종 모니터링 이벤트로 조합합니다."""

import json

DANGER_ZONE_NAME = 'danger_zone'


def build_monitoring_event(roi_alarm_message, detections_message,
                           max_age_seconds, required_labels):
    """최신 ROI 알람과 객체 검출 메시지로 JSON 직렬화 가능한 이벤트를 만듭니다."""
    roi_stamp = _stamp_seconds(roi_alarm_message.header.stamp)
    detection_stamp = _stamp_seconds(detections_message.header.stamp)
    age_seconds = abs(roi_stamp - detection_stamp)
    fresh = age_seconds <= max_age_seconds
    rois = _roi_alarms(roi_alarm_message)
    detections = _detections(detections_message)
    active_rois = [roi for roi in rois if roi['alarm']]
    matched_detections = (
        _matched_detections(detections, required_labels) if fresh else []
    )
    level = _level(active_rois, matched_detections)

    return {
        'alarm': level != 'green',
        'level': level,
        'status': 'stale' if not fresh else level,
        'age_seconds': age_seconds,
        'active_rois': active_rois,
        'matched_detections': matched_detections,
    }


def encode_monitoring_event(event):
    """모니터링 이벤트를 웹에서 바로 파싱 가능한 JSON 문자열로 변환합니다."""
    return json.dumps(event, ensure_ascii=False, separators=(',', ':'))


def _level(active_rois, matched_detections):
    if not active_rois:
        return 'green'
    if (
        any(roi['name'] == DANGER_ZONE_NAME for roi in active_rois) and
        matched_detections
    ):
        return 'red'
    return 'yellow'


def _roi_alarms(message):
    return [
        {
            'name': alarm.name,
            'alarm': bool(alarm.alarm),
            'point_count': int(alarm.point_count),
            'threshold': int(alarm.threshold),
        }
        for alarm in message.alarms
    ]


def _detections(message):
    return [
        summary
        for detection_message in message.detections
        if (summary := _detection_summary(detection_message)) is not None
    ]


def _detection_summary(detection_message):
    if not detection_message.results:
        return None

    result = detection_message.results[0].hypothesis
    return {
        'label': result.class_id,
        'score': float(result.score),
        'bbox': {
            'center_x': _bbox_center_value(detection_message.bbox, 'x'),
            'center_y': _bbox_center_value(detection_message.bbox, 'y'),
            'size_x': float(detection_message.bbox.size_x),
            'size_y': float(detection_message.bbox.size_y),
        },
    }


def _matched_detections(detections, required_labels):
    if not required_labels:
        return detections

    return [
        detection
        for detection in detections
        if detection['label'].lower() in required_labels
    ]


def _bbox_center_value(bbox, axis):
    if hasattr(bbox.center, 'position'):
        return float(getattr(bbox.center.position, axis))
    return float(getattr(bbox.center, axis))


def _stamp_seconds(stamp):
    return float(stamp.sec) + float(stamp.nanosec) / 1_000_000_000.0

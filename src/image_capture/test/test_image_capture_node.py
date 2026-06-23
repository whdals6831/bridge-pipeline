"""이미지 캡처 노드 동작 테스트입니다."""

from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch

import cv2
import pytest

from image_capture.image_capture_node import ImageCaptureNode


class FakeBridge:
    """OpenCV 이미지를 ROS 메시지처럼 생긴 객체로 변환합니다."""

    def __init__(self):
        self.calls = []

    def cv2_to_imgmsg(self, frame, encoding):
        self.calls.append((frame, encoding))
        return SimpleNamespace(header=SimpleNamespace(stamp=None, frame_id=''))


class FakeClock:
    """고정 timestamp를 제공하는 clock입니다."""

    def now(self):
        return self

    def to_msg(self):
        return 'stamp'


def make_node():
    node = object.__new__(ImageCaptureNode)
    node.image_path = '/tmp/input.jpg'
    node.image_topic = '/image/image_raw'
    node.frame_id = 'image_frame'
    node.fps = 1.0
    node.frame_timer = None
    node.destroy_timer = Mock()
    node.get_logger = Mock()
    node.get_clock = Mock(return_value=FakeClock())
    node.publisher = SimpleNamespace(published=[])
    node.publisher.publish = node.publisher.published.append
    node.bridge = FakeBridge()
    return node


def test_load_image_reads_color_image():
    node = make_node()
    frame = object()

    with patch('image_capture.image_capture_node.cv2.imread') as imread:
        imread.return_value = frame

        assert node._load_image() is frame

    imread.assert_called_once_with('/tmp/input.jpg', cv2.IMREAD_COLOR)


def test_load_image_requires_image_path():
    node = make_node()
    node.image_path = ''

    with pytest.raises(RuntimeError):
        node._load_image()

    node.get_logger.return_value.error.assert_called_once_with(
        'image_path parameter is required'
    )


def test_load_image_fails_when_image_cannot_be_read():
    node = make_node()

    with patch('image_capture.image_capture_node.cv2.imread') as imread:
        imread.return_value = None

        with pytest.raises(RuntimeError):
            node._load_image()

    node.get_logger.return_value.error.assert_called_once_with(
        'Failed to read image file: /tmp/input.jpg'
    )


def test_publish_frame_publishes_stamped_image():
    node = make_node()
    frame = object()
    node.frame = frame

    node._publish_frame()

    assert node.bridge.calls == [(frame, 'bgr8')]
    assert node.publisher.published[0].header.stamp == 'stamp'
    assert node.publisher.published[0].header.frame_id == 'image_frame'


def test_destroy_frame_timer_destroys_timer_and_clears_reference():
    node = make_node()
    timer = Mock()
    node.frame_timer = timer

    node._destroy_frame_timer()

    node.destroy_timer.assert_called_once_with(timer)
    assert node.frame_timer is None

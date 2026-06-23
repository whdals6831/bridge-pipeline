"""카메라 획득 세션을 관리합니다."""

from dataclasses import dataclass

import cv2
from cv_bridge import CvBridge


@dataclass(frozen=True)
class CaptureSettings:
    """카메라 입력과 재시도에 필요한 설정입니다."""

    camera_index: int
    width: int
    height: int
    fps: float
    retry_interval_sec: float
    frame_id: str


class OpenCVCapture:
    """OpenCV VideoCapture adapter입니다."""

    def __init__(self, camera_index):
        self._capture = cv2.VideoCapture(camera_index)

    def configure(self, settings):
        """카메라 속성을 설정합니다."""
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(settings.width))
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(settings.height))
        self._capture.set(cv2.CAP_PROP_FPS, float(settings.fps))

    def is_opened(self):
        """카메라가 열려 있는지 반환합니다."""
        return self._capture.isOpened()

    def read(self):
        """프레임 하나를 읽습니다."""
        return self._capture.read()

    def release(self):
        """카메라 리소스를 해제합니다."""
        self._capture.release()


class CameraSession:
    """카메라 입력부터 ROS 이미지 발행까지의 실행 흐름입니다."""

    def __init__(
        self,
        settings,
        publisher,
        clock,
        logger,
        timer_factory,
        timer_destroyer,
        capture_factory=OpenCVCapture,
        bridge=None,
    ):
        self._settings = settings
        self._publisher = publisher
        self._clock = clock
        self._logger = logger
        self._timer_factory = timer_factory
        self._timer_destroyer = timer_destroyer
        self._capture_factory = capture_factory
        self._bridge = bridge or CvBridge()
        self._capture = None
        self._frame_timer = None
        self._retry_timer = None
        self._warned_read_failure = False

    def start(self):
        """카메라를 열고 발행 타이머를 시작합니다."""
        self._open_capture()

    def close(self):
        """세션이 소유한 타이머와 카메라를 정리합니다."""
        self._destroy_retry_timer()
        self._release_capture()

    def _open_capture(self):
        self._destroy_retry_timer()
        self._release_capture()

        self._capture = self._capture_factory(self._settings.camera_index)
        self._capture.configure(self._settings)

        if not self._capture.is_opened():
            self._logger.error(
                'Failed to open camera index %d; retrying in %.1f seconds'
                % (
                    self._settings.camera_index,
                    self._settings.retry_interval_sec,
                )
            )
            self._release_capture()
            self._schedule_retry()
            return

        self._warned_read_failure = False
        self._frame_timer = self._timer_factory(
            1.0 / self._settings.fps,
            self._publish_frame,
        )
        self._logger.info('Camera opened')

    def _publish_frame(self):
        if self._capture is None or not self._capture.is_opened():
            self._handle_read_failure('Camera is not open')
            return

        success, frame = self._capture.read()
        if not success or frame is None:
            self._handle_read_failure('Failed to read frame from camera')
            return

        self._warned_read_failure = False
        message = self._bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        message.header.stamp = self._clock.now().to_msg()
        message.header.frame_id = self._settings.frame_id
        self._publisher.publish(message)

    def _handle_read_failure(self, message):
        if not self._warned_read_failure:
            self._logger.warn(
                '%s; retrying in %.1f seconds'
                % (message, self._settings.retry_interval_sec)
            )
            self._warned_read_failure = True

        self._release_capture()
        self._schedule_retry()

    def _schedule_retry(self):
        if self._retry_timer is None:
            self._retry_timer = self._timer_factory(
                self._settings.retry_interval_sec,
                self._open_capture,
            )

    def _release_capture(self):
        self._destroy_frame_timer()
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _destroy_frame_timer(self):
        if self._frame_timer is not None:
            self._timer_destroyer(self._frame_timer)
            self._frame_timer = None

    def _destroy_retry_timer(self):
        if self._retry_timer is not None:
            self._timer_destroyer(self._retry_timer)
            self._retry_timer = None

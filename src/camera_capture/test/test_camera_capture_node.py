"""카메라 세션 동작 테스트입니다."""

from types import SimpleNamespace

from camera_capture.camera_session import CameraSession
from camera_capture.camera_session import CaptureSettings


class FakeCapture:
    """테스트에서 제어하는 capture adapter입니다."""

    instances = []
    opened = True
    read_result = (True, object())

    def __init__(self, camera_index):
        self.camera_index = camera_index
        self.configured_with = None
        self.released = False
        FakeCapture.instances.append(self)

    def configure(self, settings):
        self.configured_with = settings

    def is_opened(self):
        return FakeCapture.opened

    def read(self):
        return FakeCapture.read_result

    def release(self):
        self.released = True


class FakeBridge:
    """OpenCV 프레임을 ROS 메시지처럼 생긴 객체로 변환합니다."""

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


class FakeLogger:
    """로그 호출을 기록합니다."""

    def __init__(self):
        self.infos = []
        self.warnings = []
        self.errors = []

    def info(self, message):
        self.infos.append(message)

    def warn(self, message):
        self.warnings.append(message)

    def error(self, message):
        self.errors.append(message)


def make_settings():
    return CaptureSettings(
        camera_index=2,
        width=800,
        height=600,
        fps=20.0,
        retry_interval_sec=3.0,
        frame_id='camera_frame',
    )


def make_session():
    timers = []
    destroyed = []
    publisher = SimpleNamespace(published=[])
    logger = FakeLogger()
    bridge = FakeBridge()

    def create_timer(period, callback):
        timer = SimpleNamespace(period=period, callback=callback)
        timers.append(timer)
        return timer

    def destroy_timer(timer):
        destroyed.append(timer)

    def publish(message):
        publisher.published.append(message)

    publisher.publish = publish
    session = CameraSession(
        settings=make_settings(),
        publisher=publisher,
        clock=FakeClock(),
        logger=logger,
        timer_factory=create_timer,
        timer_destroyer=destroy_timer,
        capture_factory=FakeCapture,
        bridge=bridge,
    )
    return session, timers, destroyed, publisher, logger, bridge


def setup_function():
    FakeCapture.instances = []
    FakeCapture.opened = True
    FakeCapture.read_result = (True, object())


def test_start_opens_capture_and_creates_frame_timer():
    session, timers, _, _, logger, _ = make_session()

    session.start()

    assert len(FakeCapture.instances) == 1
    assert FakeCapture.instances[0].camera_index == 2
    assert FakeCapture.instances[0].configured_with == make_settings()
    assert timers[0].period == 0.05
    assert logger.infos == ['Camera opened']


def test_start_failure_releases_capture_and_schedules_retry():
    FakeCapture.opened = False
    session, timers, _, _, logger, _ = make_session()

    session.start()

    assert FakeCapture.instances[0].released is True
    assert timers[0].period == 3.0
    assert 'Failed to open camera index 2' in logger.errors[0]


def test_retry_timer_reopens_capture_and_replaces_retry_timer():
    FakeCapture.opened = False
    session, timers, destroyed, _, _, _ = make_session()
    session.start()
    retry_timer = timers[0]

    FakeCapture.opened = True
    retry_timer.callback()

    assert destroyed == [retry_timer]
    assert len(FakeCapture.instances) == 2
    assert FakeCapture.instances[1].released is False
    assert timers[1].period == 0.05


def test_frame_timer_publishes_stamped_image():
    frame = object()
    FakeCapture.read_result = (True, frame)
    session, timers, _, publisher, _, bridge = make_session()
    session.start()

    timers[0].callback()

    assert bridge.calls == [(frame, 'bgr8')]
    assert publisher.published[0].header.stamp == 'stamp'
    assert publisher.published[0].header.frame_id == 'camera_frame'


def test_read_failure_releases_capture_and_replaces_frame_timer_with_retry():
    FakeCapture.read_result = (False, None)
    session, timers, destroyed, _, logger, _ = make_session()
    session.start()
    frame_timer = timers[0]

    frame_timer.callback()

    assert FakeCapture.instances[0].released is True
    assert destroyed == [frame_timer]
    assert timers[1].period == 3.0
    assert 'Failed to read frame from camera' in logger.warnings[0]


def test_close_destroys_timers_and_releases_capture():
    session, timers, destroyed, _, _, _ = make_session()
    session.start()
    frame_timer = timers[0]

    session.close()

    assert destroyed == [frame_timer]
    assert FakeCapture.instances[0].released is True


def test_close_destroys_retry_timer_after_open_failure():
    FakeCapture.opened = False
    session, timers, destroyed, _, _, _ = make_session()
    session.start()
    retry_timer = timers[0]

    session.close()

    assert destroyed == [retry_timer]

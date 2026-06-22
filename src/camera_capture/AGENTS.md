# AGENTS.md

## Module Context

`camera_capture`는 로컬 OpenCV 카메라에서 프레임을 읽어 `sensor_msgs/Image`로 발행하는 `ament_python` ROS 2 패키지다. 카메라 획득, 재시도 동작, 런치 인자, 이미지 토픽 설정을 담당한다.

## Tech Stack & Constraints

- 런타임 의존성: `rclpy`, `sensor_msgs`, `cv_bridge`, `python3-opencv`, `launch`, `launch_ros`.
- 측정된 변경 사유가 없다면 카메라 이미지 발행에는 `qos_profile_sensor_data`를 사용한다.
- 카메라 설정은 ROS 파라미터로 유지하고 런치 인자와 맞춘다.
- 런치 파일은 `setup.py`의 `data_files`로 설치한다. 콘솔 엔트리 포인트는 `setup.cfg`를 통해 `lib/camera_capture` 아래에 설치되어야 한다.

## Implementation Patterns

- 노드 엔트리 포인트: `camera_capture.camera_capture_node:main`.
- 런치 파일 이름 패턴: `launch/*.launch.py`.
- 타이머와 카메라 정리 로직은 리소스를 destroy/release한 뒤 객체 참조를 비워야 한다.
- 숫자형 ROS 파라미터는 타이머나 재시도 간격에 사용하기 전에 검증한다.
- OpenCV 프레임은 `CvBridge().cv2_to_imgmsg(frame, encoding='bgr8')`로 변환하고 timestamp와 `frame_id`를 모두 설정한다.

## Testing Strategy

- 패키지 테스트 명령: `colcon test --packages-select camera_capture --event-handlers console_direct+`
- 결과 확인: `colcon test-result --verbose`
- 전체 `rclpy` 초기화가 필요 없으면 mock으로 ROS 리소스 관리 로직을 격리해 테스트한다.
- 재시도, 타이머 정리, 캡처 해제 경로가 바뀌면 해당 동작 테스트를 추가한다.

## Local Golden Rules

- 재시도하거나 노드를 파괴하기 전에 `cv2.VideoCapture`를 해제한다.
- 기존 프레임 타이머와 재시도 타이머는 교체 전에 destroy한다.
- 런치 기본값과 노드 파라미터 기본값을 일치시킨다.
- 단위 테스트에서 실제 하드웨어 카메라를 열지 않는다.
- 유효한 ROS timestamp와 frame ID 없이 프레임을 발행하지 않는다.

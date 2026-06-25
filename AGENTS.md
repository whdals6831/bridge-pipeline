# AGENTS.md

## Operational Commands

- 전체 패키지 빌드: `colcon build --symlink-install`
- 단일 패키지 빌드: `colcon build --symlink-install --packages-select <package_name>`
- 전체 테스트 실행: `colcon test --event-handlers console_direct+`
- 단일 패키지 테스트 실행: `colcon test --packages-select <package_name> --event-handlers console_direct+`
- 테스트 결과 확인: `colcon test-result --verbose`
- 빌드 후 워크스페이스 로드: zsh는 `source install/setup.zsh`, bash는 `source install/setup.bash`
- 워크스페이스 로드 후 카메라 런치 실행: `ros2 launch camera_capture camera_capture.launch.py`
- 워크스페이스 로드 후 비디오 파일 런치 실행: `ros2 launch video_capture video_capture.launch.py video_path:=<video_path>`
- 워크스페이스 로드 후 정적 이미지 런치 실행: `ros2 launch image_capture image_capture.launch.py image_path:=<image_path>`
- 워크스페이스 로드 후 YOLO 탐지 런치 실행: `ros2 launch object_detector yolo_detector.launch.py input_image_topic:=<input_image_topic> model_paths:=<model_path>[,<model_path>...]`
- 다중 YOLO 모델 실행 예시: `ros2 launch object_detector yolo_detector.launch.py model_paths:=yolo11n.pt,/path/to/custom_best.pt duplicate_iou_threshold:=0.7`
- 워크스페이스 로드 후 라이다 전처리 런치 실행: `ros2 launch lidar_preprocessor lidar_preprocessor.launch.py input_topic:=<point_cloud_topic>`

## Golden Rules

### Immutable

- 이 저장소는 ROS 2 colcon 워크스페이스로 취급한다. 패키지 코드는 `src/<package_name>` 아래에 둔다.
- `build/`, `install/`, `log/`의 생성 결과물은 수정하지 않는다.
- `__pycache__/`, `.pytest_cache/`, `.DS_Store`, colcon 생성 결과물, 모델 weight 파일은 커밋하지 않는다.
- 런타임 의존성, 런치 파일, 콘솔 스크립트, 설치 데이터를 추가할 때 ROS 패키지 메타데이터를 함께 갱신한다.
- 장비별 카메라 디바이스, 로컬 절대 경로, 비밀값을 하드코딩하지 않는다.

### Do's & Don'ts

- `setup.py`, `setup.cfg`, `package.xml`에 이미 적용된 `ament_python` 패키지 관례를 따른다.
- 런타임 설정은 ROS 파라미터와 런치 인자를 우선 사용한다.
- 의도적인 동작 변경이 아니라면 토픽 이름, 프레임 ID, QoS 선택을 유지한다.
- 테스트는 `colcon test`로 실행 가능하게 유지한다. 직접 `pytest` 실행은 좁은 범위의 로컬 디버깅에만 사용한다.
- 타이머, 캡처, 퍼블리셔, 서브스크립션 같은 리소스의 ROS 생명주기 정리를 우회하지 않는다.
- 패키지 경계에서 필요하지 않다면 새 패키지 매니저나 의존성 체계를 추가하지 않는다.

## Project Context

이 워크스페이스는 카메라/이미지/비디오 입력, 라이다 점군 전처리, 후속 탐지를 위한 ROS 2 기반 추론 파이프라인을 구현한다. 현재 패키지는 초기 단계이므로 작고 테스트 가능하며 ROS 관례에 맞게 유지한다.

Tech stack: ROS 2, colcon, ament_python, ament_cmake, Python, C++, rclpy, rclcpp, OpenCV, cv_bridge, PCL, pcl_conversions, sensor_msgs, vision_msgs, std_msgs, Ultralytics YOLO, pytest.

## Standards & References

- Python 스타일은 패키지별 `ament_flake8`, `ament_pep257` 테스트로 검증한다.
- Python 주석과 docstring은 특별한 이유가 없으면 한국어로 작성한다.
- 에이전트가 어떤 스킬을 사용하든 사용자에게 출력하는 설명, 진행 상황, 최종 응답은 한국어로 작성한다. 코드, 명령어, 로그, 식별자는 원문을 유지한다.
- 커밋 메시지는 가능하면 한국어 Conventional Commits 형식을 따른다. 예: `feat(camera_capture): 카메라 캡처 노드 추가`
- 패키지 동작을 바꾸기 전에 해당 패키지의 `AGENTS.md`가 있으면 먼저 확인한다.
- 코드와 이 규칙이 어긋나면 같은 변경에서 관련 `AGENTS.md` 갱신을 수행하거나 제안한다.

## Context Map

- **[카메라 캡처 패키지](./src/camera_capture/AGENTS.md)** — 카메라 노드, OpenCV 캡처, 이미지 발행, 카메라 런치 변경 시.
- **[비디오 파일 캡처 패키지](./src/video_capture/AGENTS.md)** — 로컬 비디오 파일 입력, 반복 재생, `/video/image_raw` 발행 변경 시.
- **[정적 이미지 캡처 패키지](./src/image_capture/AGENTS.md)** — 단일 이미지 파일 반복 발행, `/image/image_raw` 토픽, 이미지 런치 변경 시.
- **[객체 탐지 패키지](./src/object_detector/AGENTS.md)** — 탐지 패키지 스캐폴딩, 메시지 의존성, 향후 탐지 노드 변경 시.
- **[라이다 전처리 패키지](./src/lidar_preprocessor/AGENTS.md)** — PointCloud2 구독, PCL 다운샘플링, 도로 바닥 제거, 다중 ROI 알람/마커 변경 시.

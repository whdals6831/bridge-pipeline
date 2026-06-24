# AGENTS.md

## Module Context

`object_detector`는 카메라 이미지 토픽을 구독해 하나 이상의 Ultralytics YOLO 모델 결과를 `vision_msgs/Detection2DArray`로 발행하는 `ament_python` ROS 2 패키지다. 선택적으로 중복 제거가 끝난 탐지 박스가 그려진 annotated image도 발행한다.

## Tech Stack & Constraints

- 현재 선언된 런타임 의존성: `rclpy`, `sensor_msgs`, `std_msgs`, `vision_msgs`, `cv_bridge`, `python3-opencv`, `launch`, `launch_ros`.
- Python 설치 의존성에는 `ultralytics`가 포함되어 있다. 의존성 추가나 제거 시 `package.xml`, `setup.py`, 관련 테스트를 함께 확인한다.
- 콘솔 스크립트는 `setup.py`에 등록하고 `setup.cfg`를 통해 `lib/object_detector` 아래에 설치한다.
- 탐지 런타임 설정은 모듈 전역값이 아니라 ROS 파라미터와 런치 인자로 노출한다.

## Implementation Patterns

- Python 모듈은 `object_detector/` 아래에, 테스트는 `test/` 아래에 둔다.
- 노드 엔트리 포인트: `object_detector.yolo_detector_node:main`.
- 런치 파일 이름 패턴: `launch/*.launch.py`.
- 퍼블리셔와 서브스크립션에는 명시적인 ROS 메시지 타입을 사용한다. 새 메시지 패키지를 쓰면 `package.xml`도 갱신한다.
- 입력 이미지는 기본적으로 `/camera/image_raw`에서 구독하고 탐지 결과는 `/detections`, annotated image는 `/detections/image`로 발행한다. 의도적인 계약 변경이 아니면 기본 토픽을 유지한다.
- `model_paths`, `confidence_threshold`, `iou_threshold`, `duplicate_iou_threshold`, `image_size`, `device`, `publish_annotated_image`는 노드 파라미터와 런치 인자 양쪽 기본값을 맞춘다.
- `model_paths`는 콤마 구분 문자열로 받는다. 모델이 1개여도 동일한 다중 모델 경로를 사용한다.
- 여러 모델 결과는 같은 `label`끼리만 중복 제거한다. label 비교는 대소문자를 무시하고, IoU가 `duplicate_iou_threshold` 이상이면 confidence가 높은 Detection만 유지한다.
- annotated image는 Ultralytics 단일 결과 `plot()`이 아니라 최종 병합된 `Detection` 목록을 기준으로 그린다.
- 런치 파일은 `camera_capture` 패키지 패턴을 따르고 `setup.py` `data_files`에 포함한다.

## Testing Strategy

- 패키지 테스트 명령: `colcon test --packages-select object_detector --event-handlers console_direct+`
- 결과 확인: `colcon test-result --verbose`
- YOLO 결과 변환은 Ultralytics 대역 객체나 작은 fixture로 테스트한다.
- 다중 모델 병합과 중복 제거는 모델 로드 없이 `Detection` fixture로 테스트한다.
- ROS 메시지 변환은 `Detection` 값으로 직접 테스트해 모델 로드와 추론을 분리한다.
- 기본 테스트가 카메라 토픽, GPU, 네트워크 다운로드, 로컬 모델 weight를 요구하지 않게 한다.

## Local Golden Rules

- 패키지 메타데이터와 명확한 런타임 경로 없이 무거운 추론 의존성을 도입하지 않는다.
- `camera_capture`가 항상 실행 중이라고 가정하지 않는다. 입력 토픽 누락이나 지연을 견고하게 처리한다.
- `Detection` 내부 표현과 `vision_msgs` 변환 로직을 섞지 않는다. 모델 출력 변환은 `yolo_detector.py`, ROS 메시지 변환은 노드 모듈에 둔다.
- 클래스 ID는 모델마다 충돌할 수 있으므로 중복 제거의 의미 기준으로 사용하지 않는다. 최종 비교 기준은 정규화된 label 문자열이다.
- `vision_msgs` 버전별 `BoundingBox2D.center` 구조 차이를 고려한 호환 로직을 제거하지 않는다.
- 모델 weight, 생성 데이터셋, 큰 바이너리 산출물을 이 패키지나 저장소 루트에 커밋하지 않는다.

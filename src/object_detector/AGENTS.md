# AGENTS.md

## Module Context

`object_detector`는 perception 출력과 탐지 노드 작업을 위한 `ament_python` ROS 2 패키지다. 현재는 패키지 스캐폴딩과 메시지 의존성만 있으며 콘솔 스크립트 엔트리 포인트는 없다.

## Tech Stack & Constraints

- 현재 선언된 런타임 의존성: `rclpy`, `std_msgs`.
- 이미지, 비전, 모델, OpenCV 의존성은 해당 코드가 도입될 때만 `package.xml`과 `setup.py`에 추가한다.
- 콘솔 스크립트는 `setup.py`에 등록하고 `setup.cfg`를 통해 `lib/object_detector` 아래에 설치한다.
- 탐지 런타임 설정은 모듈 전역값이 아니라 ROS 파라미터로 노출한다.

## Implementation Patterns

- Python 모듈은 `object_detector/` 아래에, 테스트는 `test/` 아래에 둔다.
- 퍼블리셔와 서브스크립션에는 명시적인 ROS 메시지 타입을 사용한다. 새 메시지 패키지를 쓰면 `package.xml`도 갱신한다.
- 모델 경로, threshold, 토픽 이름은 나중에 런치 파일에서 덮어쓸 수 있도록 파라미터화한다.
- 런치 파일을 추가할 경우 `camera_capture` 패키지 패턴을 따르고 `setup.py` `data_files`에 포함한다.

## Testing Strategy

- 패키지 테스트 명령: `colcon test --packages-select object_detector --event-handlers console_direct+`
- 결과 확인: `colcon test-result --verbose`
- 탐지 코드를 하드웨어, 카메라 토픽, 모델 파일에 연결하기 전에 단위 테스트를 추가한다.
- 추론 경계는 mock 또는 작은 fixture로 테스트한다. 기본 테스트가 로컬 모델 weight를 요구하지 않게 한다.

## Local Golden Rules

- 패키지 메타데이터와 명확한 런타임 경로 없이 무거운 추론 의존성을 도입하지 않는다.
- `camera_capture`가 항상 실행 중이라고 가정하지 않는다. 입력 토픽 누락이나 지연을 견고하게 처리한다.
- 런치 orchestration을 추가하기 전에 메시지 계약을 명시적이고 테스트 가능하게 만든다.
- 모델 weight, 생성 데이터셋, 큰 바이너리 산출물을 이 패키지에 커밋하지 않는다.

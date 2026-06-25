# AGENTS.md

## Module Context

`lidar_preprocessor`는 외부 `sensor_msgs/PointCloud2` 라이다 토픽을 구독해 PCL 기반 다운샘플링과 도로 바닥 제거 결과를 RViz 확인용 토픽으로 발행하는 `ament_cmake` ROS 2 패키지다.

## Tech Stack & Constraints

- 런타임 의존성: `rclcpp`, `sensor_msgs`, `PCL`, `pcl_conversions`, `launch`, `launch_ros`.
- 이 패키지는 C++/`ament_cmake` 기반이다. 기존 Python 패키지의 `setup.py`/`setup.cfg` 패턴을 가져오지 않는다.
- 입력 토픽, 최종 출력 토픽, 전처리 on/off, voxel 크기, PMF 파라미터는 ROS 파라미터와 런치 인자로 유지한다.
- 기본 입력 토픽은 `/points_raw`이며 실제 센서 토픽은 launch 인자로 바꾼다.

## Implementation Patterns

- 노드 실행 파일 이름: `lidar_preprocessor_node`.
- 런치 파일 이름 패턴: `launch/*.launch.py`.
- 런치 파일은 `CMakeLists.txt`의 `install(DIRECTORY launch ...)`로 설치한다.
- `PointCloud2` 변환은 `pcl_conversions`를 사용한다.
- 다운샘플링은 PCL `VoxelGrid<pcl::PointXYZ>`를 사용한다.
- 기본 발행 토픽은 최종 전처리 결과인 `/lidar/points_preprocessed`만 유지한다.
- 최종 전처리 결과는 활성화된 옵션에 따라 `다운샘플링 -> 도로 바닥 제거` 순서로 만든다.

## Testing Strategy

- 패키지 빌드 명령: `colcon build --symlink-install --packages-select lidar_preprocessor`
- 패키지 테스트 명령: `colcon test --packages-select lidar_preprocessor --event-handlers console_direct+`
- 결과 확인: `colcon test-result --verbose`
- 토픽 계약이나 파라미터 기본값을 바꾸면 launch 인자와 노드 기본값을 함께 확인한다.

## Local Golden Rules

- plane segmentation이나 복잡한 지면 모델은 PMF 방식이 부족할 때만 추가한다.
- `PointCloud2` header는 출력 메시지에 유지해 RViz fixed frame 확인을 깨지 않는다.
- 센서별 토픽명, frame ID, 장착 높이를 코드에 하드코딩하지 않는다.
- PCL 의존성을 추가/변경하면 `package.xml`과 `CMakeLists.txt`를 함께 갱신한다.
- RViz 튜닝을 위해 단독 다운샘플, 단독 바닥 제거, 최종 결과 토픽을 유지한다.

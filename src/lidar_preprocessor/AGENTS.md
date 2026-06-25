# AGENTS.md

## Module Context

`lidar_preprocessor`는 외부 `sensor_msgs/PointCloud2` 라이다 토픽을 구독해 PCL 기반 다운샘플링, 도로 바닥 제거, 다중 ROI 포인트 카운트 알람을 수행하는 `ament_cmake` ROS 2 패키지다.

## Tech Stack & Constraints

- 런타임 의존성: `rclcpp`, `sensor_msgs`, `std_msgs`, `visualization_msgs`, `PCL`, `pcl_conversions`, `launch`, `launch_ros`, `rosidl_default_runtime`.
- 이 패키지는 C++/`ament_cmake` 기반이다. 기존 Python 패키지의 `setup.py`/`setup.cfg` 패턴을 가져오지 않는다.
- 입력 토픽, 최종 출력 토픽, ROI 알람/마커 토픽, 전처리 on/off, voxel 크기, PMF 파라미터, ROI 경계/임계값은 ROS 파라미터와 런치 인자로 유지한다.
- 기본 입력 토픽은 `/points_raw`이며 실제 센서 토픽은 launch 인자로 바꾼다.
- ROI 알람은 `enable_roi_alarm`이 `true`일 때만 `/lidar/roi_alarm`의 `RoiAlarmArray`와 `/lidar/roi_marker`의 `visualization_msgs/MarkerArray`를 발행한다.

## Implementation Patterns

- 노드 실행 파일 이름: `lidar_preprocessor_node`.
- 런치 파일 이름 패턴: `launch/*.launch.py`.
- 런치 파일은 `CMakeLists.txt`의 `install(DIRECTORY launch ...)`로 설치한다.
- 커스텀 메시지는 `msg/*.msg`에 두고 `rosidl_generate_interfaces()`와 `package.xml`의 generator/runtime 의존성을 함께 유지한다.
- `PointCloud2` 변환은 `pcl_conversions`를 사용한다.
- 다운샘플링은 PCL `VoxelGrid<pcl::PointXYZ>`를 사용한다.
- 최종 전처리 결과는 활성화된 옵션에 따라 `다운샘플링 -> 도로 바닥 제거` 순서로 만든다.
- ROI 알람은 최종 전처리 결과 클라우드 기준으로 계산한다.
- 다중 ROI 설정은 `roi_names`, `roi_min_xs`, `roi_max_xs`, `roi_min_ys`, `roi_max_ys`, `roi_min_zs`, `roi_max_zs`, `roi_point_thresholds` 배열의 같은 인덱스를 하나의 ROI로 취급한다.
- ROI 배열 길이가 서로 다르면 알람을 비활성화하는 기존 실패 방식을 유지한다.
- RViz ROI 표시는 `MarkerArray`의 `CUBE` 마커를 사용하고, 알람 상태 색상은 초록/빨강 관례를 유지한다.

## Testing Strategy

- 패키지 빌드 명령: `colcon build --symlink-install --packages-select lidar_preprocessor`
- 패키지 테스트 명령: `colcon test --packages-select lidar_preprocessor --event-handlers console_direct+`
- 결과 확인: `colcon test-result --verbose`
- 토픽 계약이나 파라미터 기본값을 바꾸면 launch 인자와 노드 기본값을 함께 확인한다.
- ROI 메시지 필드나 토픽명을 바꾸면 `rosidl_generate_interfaces()`, `package.xml`, launch 인자, 노드 publisher 타입을 함께 확인한다.

## Local Golden Rules

- plane segmentation이나 복잡한 지면 모델은 PMF 방식이 부족할 때만 추가한다.
- `PointCloud2` header는 출력 메시지에 유지해 RViz fixed frame 확인을 깨지 않는다.
- `RoiAlarmArray`와 ROI marker도 입력 `PointCloud2` header를 그대로 사용한다.
- 센서별 토픽명, frame ID, 장착 높이를 코드에 하드코딩하지 않는다.
- PCL 의존성을 추가/변경하면 `package.xml`과 `CMakeLists.txt`를 함께 갱신한다.
- ROI는 축 정렬 박스 기준이다. 회전 ROI, 폴리곤 ROI, 추적 상태는 실제 요구가 생길 때만 추가한다.
- ROI 기본값을 바꿀 때는 노드 기본값과 launch 기본값을 같이 맞춘다.

"""라이다 ROI 알람과 객체 검출 결과를 최종 모니터링 알람으로 발행합니다."""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String

from lidar_preprocessor.msg import RoiAlarmArray
from monitoring_fusion.monitoring_alarm import build_monitoring_event
from monitoring_fusion.monitoring_alarm import encode_monitoring_event
from monitoring_fusion.parameters import declare_fusion_parameters
from monitoring_fusion.parameters import parse_required_labels
from monitoring_fusion.parameters import read_fusion_parameters
from vision_msgs.msg import Detection2DArray


class MonitoringFusionNode(Node):
    """센서별 판단 결과를 웹 표시용 최종 알람 이벤트로 조합합니다."""

    def __init__(self):
        """ROS 파라미터를 읽고 구독/발행 리소스를 생성합니다."""
        super().__init__('monitoring_fusion')

        declare_fusion_parameters(self)
        parameters = read_fusion_parameters(self)
        self.max_age_seconds = parameters.max_age_seconds
        self.required_labels = parse_required_labels(
            parameters.required_detection_labels,
        )
        self.latest_roi_alarm = None
        self.latest_detections = None

        self.alarm_publisher = self.create_publisher(
            String,
            parameters.output_topic,
            10,
        )
        self.roi_subscription = self.create_subscription(
            RoiAlarmArray,
            parameters.roi_alarm_topic,
            self._roi_alarm_callback,
            qos_profile_sensor_data,
        )
        self.detections_subscription = self.create_subscription(
            Detection2DArray,
            parameters.detections_topic,
            self._detections_callback,
            10,
        )

        self.get_logger().info(
            'Fusing %s and %s into %s'
            % (
                parameters.roi_alarm_topic,
                parameters.detections_topic,
                parameters.output_topic,
            )
        )

    def _roi_alarm_callback(self, message):
        self.latest_roi_alarm = message
        self._publish_if_ready()

    def _detections_callback(self, message):
        self.latest_detections = message
        self._publish_if_ready()

    def _publish_if_ready(self):
        if self.latest_roi_alarm is None or self.latest_detections is None:
            return

        event = build_monitoring_event(
            self.latest_roi_alarm,
            self.latest_detections,
            self.max_age_seconds,
            self.required_labels,
        )
        message = String()
        message.data = encode_monitoring_event(event)
        self.alarm_publisher.publish(message)


def main(args=None):
    """모니터링 fusion 노드를 시작합니다."""
    rclpy.init(args=args)
    node = MonitoringFusionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

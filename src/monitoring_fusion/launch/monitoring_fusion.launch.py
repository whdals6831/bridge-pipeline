"""모니터링 fusion 노드를 실행합니다."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from monitoring_fusion.parameters import PARAMETER_SPECS


def generate_launch_description():
    """monitoring_fusion 실행 설명을 생성합니다."""
    launch_arguments = [
        DeclareLaunchArgument(
            spec.name,
            default_value=spec.launch_default,
        )
        for spec in PARAMETER_SPECS
    ]
    parameters = {
        spec.name: _launch_parameter_value(spec)
        for spec in PARAMETER_SPECS
    }

    return LaunchDescription(launch_arguments + [
        Node(
            package='monitoring_fusion',
            executable='monitoring_fusion_node',
            name='monitoring_fusion',
            output='screen',
            parameters=[parameters],
        ),
    ])


def _launch_parameter_value(spec):
    configuration = LaunchConfiguration(spec.name)
    if spec.value_type is None:
        return configuration
    return ParameterValue(configuration, value_type=spec.value_type)

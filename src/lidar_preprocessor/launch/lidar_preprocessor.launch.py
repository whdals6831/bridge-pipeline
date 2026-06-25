from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


PARAMETER_TYPES = {
    "input_topic": str,
    "preprocessed_topic": str,
    "roi_alarm_topic": str,
    "roi_marker_topic": str,
    "enable_downsample": bool,
    "enable_ground_removal": bool,
    "enable_roi_alarm": bool,
    "stamp_outputs_with_node_time": bool,
    "voxel_leaf_size": float,
    "max_window_size": int,
    "slope": float,
    "initial_distance": float,
    "max_distance": float,
    "roi_names": list[str],
    "roi_min_xs": list[float],
    "roi_max_xs": list[float],
    "roi_min_ys": list[float],
    "roi_max_ys": list[float],
    "roi_min_zs": list[float],
    "roi_max_zs": list[float],
    "roi_point_thresholds": list[int],
}


def launch_setup(context, *args, **kwargs):
    parameters = {}
    for name, value_type in PARAMETER_TYPES.items():
        value = LaunchConfiguration(name).perform(context)
        if value != "":
            parameters[name] = ParameterValue(value, value_type=value_type)

    return [
        Node(
            package="lidar_preprocessor",
            executable="lidar_preprocessor_node",
            name="lidar_preprocessor_node",
            parameters=[parameters],
            output="screen",
        )
    ]


def generate_launch_description():
    return LaunchDescription(
        [DeclareLaunchArgument(name, default_value="") for name in PARAMETER_TYPES]
        + [OpaqueFunction(function=launch_setup)]
    )

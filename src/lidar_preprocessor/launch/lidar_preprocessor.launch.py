from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    input_topic = LaunchConfiguration("input_topic")
    preprocessed_topic = LaunchConfiguration("preprocessed_topic")
    roi_alarm_topic = LaunchConfiguration("roi_alarm_topic")
    roi_marker_topic = LaunchConfiguration("roi_marker_topic")
    enable_downsample = LaunchConfiguration("enable_downsample")
    enable_ground_removal = LaunchConfiguration("enable_ground_removal")
    enable_roi_alarm = LaunchConfiguration("enable_roi_alarm")
    stamp_outputs_with_node_time = LaunchConfiguration("stamp_outputs_with_node_time")
    voxel_leaf_size = LaunchConfiguration("voxel_leaf_size")
    max_window_size = LaunchConfiguration("max_window_size")
    slope = LaunchConfiguration("slope")
    initial_distance = LaunchConfiguration("initial_distance")
    max_distance = LaunchConfiguration("max_distance")
    roi_names = LaunchConfiguration("roi_names")
    roi_min_xs = LaunchConfiguration("roi_min_xs")
    roi_max_xs = LaunchConfiguration("roi_max_xs")
    roi_min_ys = LaunchConfiguration("roi_min_ys")
    roi_max_ys = LaunchConfiguration("roi_max_ys")
    roi_min_zs = LaunchConfiguration("roi_min_zs")
    roi_max_zs = LaunchConfiguration("roi_max_zs")
    roi_point_thresholds = LaunchConfiguration("roi_point_thresholds")

    return LaunchDescription(
        [
            DeclareLaunchArgument("input_topic", default_value="/points_raw"),
            DeclareLaunchArgument(
                "preprocessed_topic",
                default_value="/lidar/points_preprocessed",
            ),
            DeclareLaunchArgument("roi_alarm_topic", default_value="/lidar/roi_alarm"),
            DeclareLaunchArgument("roi_marker_topic", default_value="/lidar/roi_marker"),
            DeclareLaunchArgument("enable_downsample", default_value="false"),
            DeclareLaunchArgument("enable_ground_removal", default_value="false"),
            DeclareLaunchArgument("enable_roi_alarm", default_value="false"),
            DeclareLaunchArgument("stamp_outputs_with_node_time", default_value="true"),
            DeclareLaunchArgument("voxel_leaf_size", default_value="0.1"),
            DeclareLaunchArgument("max_window_size", default_value="10"),
            DeclareLaunchArgument("slope", default_value="1.0"),
            DeclareLaunchArgument("initial_distance", default_value="0.5"),
            DeclareLaunchArgument("max_distance", default_value="50.0"),
            DeclareLaunchArgument("roi_names", default_value="['danger_zone', 'warning_zone']"),
            DeclareLaunchArgument("roi_min_xs", default_value="[0.0, 1.0]"),
            DeclareLaunchArgument("roi_max_xs", default_value="[1.0, 2.0]"),
            DeclareLaunchArgument("roi_min_ys", default_value="[0.0, 0.0]"),
            DeclareLaunchArgument("roi_max_ys", default_value="[1.0, 1.0]"),
            DeclareLaunchArgument("roi_min_zs", default_value="[0.0, 0.0]"),
            DeclareLaunchArgument("roi_max_zs", default_value="[1.0, 1.0]"),
            DeclareLaunchArgument("roi_point_thresholds", default_value="[50, 50]"),
            Node(
                package="lidar_preprocessor",
                executable="lidar_preprocessor_node",
                name="lidar_preprocessor_node",
                parameters=[
                    {
                        "input_topic": input_topic,
                        "preprocessed_topic": preprocessed_topic,
                        "roi_alarm_topic": roi_alarm_topic,
                        "roi_marker_topic": roi_marker_topic,
                        "enable_downsample": ParameterValue(
                            enable_downsample,
                            value_type=bool,
                        ),
                        "enable_ground_removal": ParameterValue(
                            enable_ground_removal,
                            value_type=bool,
                        ),
                        "enable_roi_alarm": ParameterValue(
                            enable_roi_alarm,
                            value_type=bool,
                        ),
                        "stamp_outputs_with_node_time": ParameterValue(
                            stamp_outputs_with_node_time,
                            value_type=bool,
                        ),
                        "voxel_leaf_size": ParameterValue(
                            voxel_leaf_size,
                            value_type=float,
                        ),
                        "max_window_size": ParameterValue(
                            max_window_size,
                            value_type=int,
                        ),
                        "slope": ParameterValue(
                            slope,
                            value_type=float,
                        ),
                        "initial_distance": ParameterValue(
                            initial_distance,
                            value_type=float,
                        ),
                        "max_distance": ParameterValue(
                            max_distance,
                            value_type=float,
                        ),
                        "roi_names": ParameterValue(
                            roi_names,
                            value_type=list[str],
                        ),
                        "roi_min_xs": ParameterValue(
                            roi_min_xs,
                            value_type=list[float],
                        ),
                        "roi_max_xs": ParameterValue(
                            roi_max_xs,
                            value_type=list[float],
                        ),
                        "roi_min_ys": ParameterValue(
                            roi_min_ys,
                            value_type=list[float],
                        ),
                        "roi_max_ys": ParameterValue(
                            roi_max_ys,
                            value_type=list[float],
                        ),
                        "roi_min_zs": ParameterValue(
                            roi_min_zs,
                            value_type=list[float],
                        ),
                        "roi_max_zs": ParameterValue(
                            roi_max_zs,
                            value_type=list[float],
                        ),
                        "roi_point_thresholds": ParameterValue(
                            roi_point_thresholds,
                            value_type=list[int],
                        ),
                    }
                ],
                output="screen",
            ),
        ]
    )

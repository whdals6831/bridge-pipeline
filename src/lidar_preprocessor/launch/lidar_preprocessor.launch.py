from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    input_topic = LaunchConfiguration("input_topic")
    preprocessed_topic = LaunchConfiguration("preprocessed_topic")
    enable_downsample = LaunchConfiguration("enable_downsample")
    enable_ground_removal = LaunchConfiguration("enable_ground_removal")
    voxel_leaf_size = LaunchConfiguration("voxel_leaf_size")
    max_window_size = LaunchConfiguration("max_window_size")
    slope = LaunchConfiguration("slope")
    initial_distance = LaunchConfiguration("initial_distance")
    max_distance = LaunchConfiguration("max_distance")

    return LaunchDescription(
        [
            DeclareLaunchArgument("input_topic", default_value="/points_raw"),
            DeclareLaunchArgument(
                "preprocessed_topic",
                default_value="/lidar/points_preprocessed",
            ),
            DeclareLaunchArgument("enable_downsample", default_value="true"),
            DeclareLaunchArgument("enable_ground_removal", default_value="true"),
            DeclareLaunchArgument("voxel_leaf_size", default_value="0.1"),
            DeclareLaunchArgument("max_window_size", default_value="10"),
            DeclareLaunchArgument("slope", default_value="1.0"),
            DeclareLaunchArgument("initial_distance", default_value="0.5"),
            DeclareLaunchArgument("max_distance", default_value="3.0"),
            Node(
                package="lidar_preprocessor",
                executable="lidar_preprocessor_node",
                name="lidar_preprocessor_node",
                parameters=[
                    {
                        "input_topic": input_topic,
                        "preprocessed_topic": preprocessed_topic,
                        "enable_downsample": ParameterValue(
                            enable_downsample,
                            value_type=bool,
                        ),
                        "enable_ground_removal": ParameterValue(
                            enable_ground_removal,
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
                    }
                ],
                output="screen",
            ),
        ]
    )

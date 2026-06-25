#include <memory>
#include <string>
#include <vector>

#include "lidar_preprocessor/msg/roi_alarm.hpp"
#include "lidar_preprocessor/msg/roi_alarm_array.hpp"
#include "pcl/filters/extract_indices.h"
#include "pcl/filters/voxel_grid.h"
#include "pcl/point_cloud.h"
#include "pcl/point_types.h"
#include "pcl/segmentation/progressive_morphological_filter.h"
#include "pcl_conversions/pcl_conversions.h"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "visualization_msgs/msg/marker_array.hpp"

class LidarPreprocessorNode : public rclcpp::Node
{
public:
  LidarPreprocessorNode()
  : Node("lidar_preprocessor_node")
  {
    input_topic_ = declare_parameter<std::string>("input_topic", "/points_raw");
    const auto preprocessed_topic =
      declare_parameter<std::string>("preprocessed_topic", "/lidar/points_preprocessed");
    const auto roi_alarm_topic =
      declare_parameter<std::string>("roi_alarm_topic", "/lidar/roi_alarm");
    const auto roi_marker_topic =
      declare_parameter<std::string>("roi_marker_topic", "/lidar/roi_marker");
    enable_downsample_ = declare_parameter<bool>("enable_downsample", false);
    enable_ground_removal_ = declare_parameter<bool>("enable_ground_removal", false);
    enable_roi_alarm_ = declare_parameter<bool>("enable_roi_alarm", false);
    stamp_outputs_with_node_time_ = declare_parameter<bool>("stamp_outputs_with_node_time", true);
    voxel_leaf_size_ = declare_parameter<double>("voxel_leaf_size", 0.1);
    max_window_size_ = declare_parameter<int>("max_window_size", 10);
    slope_ = declare_parameter<double>("slope", 1.0);
    initial_distance_ = declare_parameter<double>("initial_distance", 0.5);
    max_distance_ = declare_parameter<double>("max_distance", 50.0);
    roi_names_ = declare_parameter<std::vector<std::string>>(
      "roi_names",
      {"danger_zone", "warning_zone"});
    roi_min_xs_ = declare_parameter<std::vector<double>>("roi_min_xs", {0.0, 1.0});
    roi_max_xs_ = declare_parameter<std::vector<double>>("roi_max_xs", {1.0, 2.0});
    roi_min_ys_ = declare_parameter<std::vector<double>>("roi_min_ys", {0.0, 0.0});
    roi_max_ys_ = declare_parameter<std::vector<double>>("roi_max_ys", {1.0, 1.0});
    roi_min_zs_ = declare_parameter<std::vector<double>>("roi_min_zs", {0.0, 0.0});
    roi_max_zs_ = declare_parameter<std::vector<double>>("roi_max_zs", {1.0, 1.0});
    roi_point_thresholds_ = declare_parameter<std::vector<int64_t>>(
      "roi_point_thresholds",
      {50, 50});
    roi_count_ = valid_roi_count();

    const auto qos = rclcpp::SensorDataQoS();
    preprocessed_pub_ =
      create_publisher<sensor_msgs::msg::PointCloud2>(preprocessed_topic, qos);
    roi_alarm_pub_ = create_publisher<lidar_preprocessor::msg::RoiAlarmArray>(
      roi_alarm_topic, qos);
    roi_marker_pub_ = create_publisher<visualization_msgs::msg::MarkerArray>(
      roi_marker_topic, qos);
    subscription_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      input_topic_, qos,
      [this](sensor_msgs::msg::PointCloud2::ConstSharedPtr msg) {
        process(msg);
      });
  }

private:
  using PointCloud = pcl::PointCloud<pcl::PointXYZ>;

  void process(const sensor_msgs::msg::PointCloud2::ConstSharedPtr msg)
  {
    auto input = std::make_shared<PointCloud>();
    pcl::fromROSMsg(*msg, *input);

    auto preprocessed = enable_downsample_ ? downsample(input) : input;
    if (enable_ground_removal_) {
      preprocessed = remove_ground(preprocessed);
    }
    const auto header = output_header(msg->header);
    publish(*preprocessed, header, preprocessed_pub_);
    publish_roi_alarm(*preprocessed, header);
  }

  std_msgs::msg::Header output_header(const std_msgs::msg::Header & input_header) const
  {
    auto header = input_header;
    if (stamp_outputs_with_node_time_) {
      header.stamp = now();
    }
    return header;
  }

  PointCloud::Ptr downsample(const PointCloud::ConstPtr cloud) const
  {
    auto filtered = std::make_shared<PointCloud>();
    if (voxel_leaf_size_ <= 0.0) {
      *filtered = *cloud;
      return filtered;
    }

    pcl::VoxelGrid<pcl::PointXYZ> voxel_grid;
    voxel_grid.setInputCloud(cloud);
    voxel_grid.setLeafSize(voxel_leaf_size_, voxel_leaf_size_, voxel_leaf_size_);
    voxel_grid.filter(*filtered);
    return filtered;
  }

  PointCloud::Ptr remove_ground(const PointCloud::ConstPtr cloud) const
  {
    auto filtered = std::make_shared<PointCloud>();

    pcl::PointIndices::Ptr ground_indices(new pcl::PointIndices);
    pcl::ProgressiveMorphologicalFilter<pcl::PointXYZ> ground_filter;
    ground_filter.setInputCloud(cloud);
    ground_filter.setMaxWindowSize(max_window_size_);
    ground_filter.setSlope(static_cast<float>(slope_));
    ground_filter.setInitialDistance(static_cast<float>(initial_distance_));
    ground_filter.setMaxDistance(static_cast<float>(max_distance_));
    ground_filter.extract(ground_indices->indices);

    if (ground_indices->indices.empty()) {
      *filtered = *cloud;
      return filtered;
    }

    pcl::ExtractIndices<pcl::PointXYZ> extract;
    extract.setInputCloud(cloud);
    extract.setIndices(ground_indices);
    extract.setNegative(true);
    extract.filter(*filtered);
    return filtered;
  }

  void publish(
    const PointCloud & cloud,
    const std_msgs::msg::Header & header,
    const rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr & publisher) const
  {
    sensor_msgs::msg::PointCloud2 output;
    pcl::toROSMsg(cloud, output);
    output.header = header;
    publisher->publish(output);
  }

  void publish_roi_alarm(const PointCloud & cloud, const std_msgs::msg::Header & header) const
  {
    if (!enable_roi_alarm_) {
      return;
    }

    lidar_preprocessor::msg::RoiAlarmArray alarms;
    alarms.header = header;

    std::vector<bool> alarm_states;
    alarm_states.reserve(roi_count_);
    for (size_t i = 0; i < roi_count_; ++i) {
      uint32_t count = 0;
      for (const auto & point : cloud.points) {
        if (
          point.x >= roi_min_xs_[i] && point.x <= roi_max_xs_[i] &&
          point.y >= roi_min_ys_[i] && point.y <= roi_max_ys_[i] &&
          point.z >= roi_min_zs_[i] && point.z <= roi_max_zs_[i])
        {
          ++count;
        }
      }

      lidar_preprocessor::msg::RoiAlarm alarm;
      alarm.name = roi_names_[i];
      alarm.point_count = count;
      alarm.threshold = static_cast<uint32_t>(roi_point_thresholds_[i]);
      alarm.alarm = count >= alarm.threshold;
      alarm_states.push_back(alarm.alarm);
      alarms.alarms.push_back(alarm);
    }

    roi_alarm_pub_->publish(alarms);
    publish_roi_markers(header, alarm_states);
  }

  void publish_roi_markers(
    const std_msgs::msg::Header & header,
    const std::vector<bool> & alarm_states) const
  {
    visualization_msgs::msg::MarkerArray markers;
    for (size_t i = 0; i < roi_count_; ++i) {
      visualization_msgs::msg::Marker marker;
      marker.header = header;
      marker.ns = "lidar_roi";
      marker.id = static_cast<int32_t>(i);
      marker.type = visualization_msgs::msg::Marker::CUBE;
      marker.action = visualization_msgs::msg::Marker::ADD;
      marker.pose.position.x = (roi_min_xs_[i] + roi_max_xs_[i]) / 2.0;
      marker.pose.position.y = (roi_min_ys_[i] + roi_max_ys_[i]) / 2.0;
      marker.pose.position.z = (roi_min_zs_[i] + roi_max_zs_[i]) / 2.0;
      marker.pose.orientation.w = 1.0;
      marker.scale.x = roi_max_xs_[i] - roi_min_xs_[i];
      marker.scale.y = roi_max_ys_[i] - roi_min_ys_[i];
      marker.scale.z = roi_max_zs_[i] - roi_min_zs_[i];
      marker.color.r = alarm_states[i] ? 1.0F : 0.0F;
      marker.color.g = alarm_states[i] ? 0.0F : 1.0F;
      marker.color.b = 0.0F;
      marker.color.a = 0.25F;
      markers.markers.push_back(marker);
    }
    roi_marker_pub_->publish(markers);
  }

  size_t valid_roi_count() const
  {
    const auto count = roi_names_.size();
    if (
      roi_min_xs_.size() == count && roi_max_xs_.size() == count &&
      roi_min_ys_.size() == count && roi_max_ys_.size() == count &&
      roi_min_zs_.size() == count && roi_max_zs_.size() == count &&
      roi_point_thresholds_.size() == count)
    {
      return count;
    }

    RCLCPP_ERROR(
      get_logger(),
      "ROI parameter arrays must have the same length; ROI alarm is disabled.");
    return 0;
  }

  std::string input_topic_;
  bool enable_downsample_;
  bool enable_ground_removal_;
  bool enable_roi_alarm_;
  bool stamp_outputs_with_node_time_;
  double voxel_leaf_size_;
  int max_window_size_;
  double slope_;
  double initial_distance_;
  double max_distance_;
  std::vector<std::string> roi_names_;
  std::vector<double> roi_min_xs_;
  std::vector<double> roi_max_xs_;
  std::vector<double> roi_min_ys_;
  std::vector<double> roi_max_ys_;
  std::vector<double> roi_min_zs_;
  std::vector<double> roi_max_zs_;
  std::vector<int64_t> roi_point_thresholds_;
  size_t roi_count_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr subscription_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr preprocessed_pub_;
  rclcpp::Publisher<lidar_preprocessor::msg::RoiAlarmArray>::SharedPtr roi_alarm_pub_;
  rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr roi_marker_pub_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<LidarPreprocessorNode>());
  rclcpp::shutdown();
  return 0;
}

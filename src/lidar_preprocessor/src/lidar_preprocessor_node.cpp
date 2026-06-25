#include <memory>
#include <string>

#include "pcl/filters/extract_indices.h"
#include "pcl/filters/voxel_grid.h"
#include "pcl/point_cloud.h"
#include "pcl/point_types.h"
#include "pcl/segmentation/progressive_morphological_filter.h"
#include "pcl_conversions/pcl_conversions.h"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"

class LidarPreprocessorNode : public rclcpp::Node
{
public:
  LidarPreprocessorNode()
  : Node("lidar_preprocessor_node")
  {
    input_topic_ = declare_parameter<std::string>("input_topic", "/points_raw");
    const auto preprocessed_topic =
      declare_parameter<std::string>("preprocessed_topic", "/lidar/points_preprocessed");
    enable_downsample_ = declare_parameter<bool>("enable_downsample", true);
    enable_ground_removal_ = declare_parameter<bool>("enable_ground_removal", true);
    voxel_leaf_size_ = declare_parameter<double>("voxel_leaf_size", 0.1);
    max_window_size_ = declare_parameter<int>("max_window_size", 10);
    slope_ = declare_parameter<double>("slope", 1.0);
    initial_distance_ = declare_parameter<double>("initial_distance", 0.5);
    max_distance_ = declare_parameter<double>("max_distance", 3.0);

    const auto qos = rclcpp::SensorDataQoS();
    preprocessed_pub_ =
      create_publisher<sensor_msgs::msg::PointCloud2>(preprocessed_topic, qos);
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
    publish(*preprocessed, msg->header, preprocessed_pub_);
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

  std::string input_topic_;
  bool enable_downsample_;
  bool enable_ground_removal_;
  double voxel_leaf_size_;
  int max_window_size_;
  double slope_;
  double initial_distance_;
  double max_distance_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr subscription_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr preprocessed_pub_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<LidarPreprocessorNode>());
  rclcpp::shutdown();
  return 0;
}

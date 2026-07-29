#include <librealsense2/rs.hpp>

#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>

int main(int argc, char **argv) {
  const double duration_s = argc > 1 ? std::stod(argv[1]) : 60.0;
  rs2::context context;
  std::string serial;
  for (auto &&device : context.query_devices()) {
    const std::string name = device.get_info(RS2_CAMERA_INFO_NAME);
    if (name.find("T265") != std::string::npos) {
      serial = device.get_info(RS2_CAMERA_INFO_SERIAL_NUMBER);
      break;
    }
  }
  if (serial.empty()) {
    std::cerr << "T265 not found\n";
    return 2;
  }

  rs2::pipeline pipeline(context);
  rs2::config config;
  config.enable_device(serial);
  config.enable_stream(RS2_STREAM_POSE, RS2_FORMAT_6DOF);
  pipeline.start(config);

  const auto started = std::chrono::steady_clock::now();
  uint64_t samples = 0;
  uint64_t timestamp_regressions = 0;
  uint64_t frame_regressions = 0;
  uint64_t non_finite = 0;
  uint64_t invalid_quaternion = 0;
  uint64_t confidence_counts[4] = {0, 0, 0, 0};
  double first_timestamp_ms = std::numeric_limits<double>::quiet_NaN();
  double previous_timestamp_ms = -1.0;
  uint64_t previous_frame = 0;
  double max_gap_ms = 0.0;
  double min_quaternion_norm = std::numeric_limits<double>::infinity();
  double max_quaternion_norm = 0.0;

  while (std::chrono::duration<double>(
             std::chrono::steady_clock::now() - started).count() < duration_s) {
    auto frames = pipeline.wait_for_frames(2000);
    auto pose_frame = frames.first_or_default(RS2_STREAM_POSE).as<rs2::pose_frame>();
    if (!pose_frame) {
      continue;
    }
    const auto pose = pose_frame.get_pose_data();
    const double timestamp_ms = pose_frame.get_timestamp();
    const uint64_t frame_number = pose_frame.get_frame_number();
    const double qnorm = std::sqrt(
        pose.rotation.x * pose.rotation.x + pose.rotation.y * pose.rotation.y +
        pose.rotation.z * pose.rotation.z + pose.rotation.w * pose.rotation.w);
    const double values[] = {
        timestamp_ms,
        pose.translation.x, pose.translation.y, pose.translation.z,
        pose.velocity.x, pose.velocity.y, pose.velocity.z,
        pose.rotation.x, pose.rotation.y, pose.rotation.z, pose.rotation.w,
    };
    for (const double value : values) {
      if (!std::isfinite(value)) {
        ++non_finite;
      }
    }
    if (!std::isfinite(qnorm) || qnorm < 0.99 || qnorm > 1.01) {
      ++invalid_quaternion;
    }
    min_quaternion_norm = std::min(min_quaternion_norm, qnorm);
    max_quaternion_norm = std::max(max_quaternion_norm, qnorm);
    if (samples == 0) {
      first_timestamp_ms = timestamp_ms;
    } else {
      if (timestamp_ms <= previous_timestamp_ms) {
        ++timestamp_regressions;
      } else {
        max_gap_ms = std::max(max_gap_ms, timestamp_ms - previous_timestamp_ms);
      }
      if (frame_number <= previous_frame) {
        ++frame_regressions;
      }
    }
    previous_timestamp_ms = timestamp_ms;
    previous_frame = frame_number;
    if (pose.tracker_confidence <= 3) {
      ++confidence_counts[pose.tracker_confidence];
    }
    ++samples;
  }
  pipeline.stop();
  const double elapsed_s = std::chrono::duration<double>(
      std::chrono::steady_clock::now() - started).count();
  const double device_span_s =
      samples > 1 ? (previous_timestamp_ms - first_timestamp_ms) / 1000.0 : 0.0;
  const double rate_hz = device_span_s > 0.0 ? (samples - 1) / device_span_s : 0.0;

  std::cout << std::fixed << std::setprecision(6)
            << "{\n"
            << "  \"serial\": \"" << serial << "\",\n"
            << "  \"elapsed_s\": " << elapsed_s << ",\n"
            << "  \"samples\": " << samples << ",\n"
            << "  \"device_span_s\": " << device_span_s << ",\n"
            << "  \"rate_hz\": " << rate_hz << ",\n"
            << "  \"max_gap_ms\": " << max_gap_ms << ",\n"
            << "  \"timestamp_regressions\": " << timestamp_regressions << ",\n"
            << "  \"frame_regressions\": " << frame_regressions << ",\n"
            << "  \"non_finite_values\": " << non_finite << ",\n"
            << "  \"invalid_quaternion_samples\": " << invalid_quaternion << ",\n"
            << "  \"quaternion_norm_min\": " << min_quaternion_norm << ",\n"
            << "  \"quaternion_norm_max\": " << max_quaternion_norm << ",\n"
            << "  \"tracker_confidence_counts\": ["
            << confidence_counts[0] << ", " << confidence_counts[1] << ", "
            << confidence_counts[2] << ", " << confidence_counts[3] << "]\n"
            << "}\n";
  return samples > 0 && timestamp_regressions == 0 &&
                 frame_regressions == 0 && non_finite == 0 &&
                 invalid_quaternion == 0
             ? 0
             : 3;
}

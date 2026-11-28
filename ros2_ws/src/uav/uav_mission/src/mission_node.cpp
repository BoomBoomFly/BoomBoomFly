#include "uav_mission/mission_node.hpp"

#include <cmath>
#include <functional>
#include <stdexcept>
#include <utility>

#include <diagnostic_msgs/msg/diagnostic_status.hpp>

#include "uav_mission/vio_health.hpp"

namespace uav_mission
{

MissionNode::MissionNode()
: Node("uav_mission")
{
  FlightTaskConfig config;
  config.takeoff_height_m = declare_parameter<double>("takeoff_height_m", 1.0);
  config.horizontal_tolerance_m = declare_parameter<double>("horizontal_tolerance_m", 0.2);
  config.vertical_tolerance_m = declare_parameter<double>("vertical_tolerance_m", 0.15);
  config.stable_duration_s = declare_parameter<double>("stable_duration_s", 2.0);
  config.hover_duration_s = declare_parameter<double>("hover_duration_s", 10.0);
  config.prestream_s = declare_parameter<double>("prestream_s", 1.2);
  config.ready_timeout_s = declare_parameter<double>("ready_timeout_s", 30.0);
  config.command_timeout_s = declare_parameter<double>("command_timeout_s", 7.0);
  config.takeoff_timeout_s = declare_parameter<double>("takeoff_timeout_s", 30.0);
  config.landing_timeout_s = declare_parameter<double>("landing_timeout_s", 45.0);
  require_vio_health_ = config.require_vio_health =
    declare_parameter<bool>("require_vio_health", false);
  vio_health_timeout_s_ = declare_parameter<double>("vio_health_timeout_s", 2.0);
  state_timeout_s_ = declare_parameter<double>("state_timeout_s", 1.0);
  if (!std::isfinite(config.takeoff_height_m) || config.takeoff_height_m <= 0.0 ||
    !std::isfinite(config.horizontal_tolerance_m) || config.horizontal_tolerance_m <= 0.0 ||
    !std::isfinite(config.vertical_tolerance_m) || config.vertical_tolerance_m <= 0.0 ||
    !std::isfinite(config.stable_duration_s) || config.stable_duration_s <= 0.0 ||
    !std::isfinite(config.hover_duration_s) || config.hover_duration_s <= 0.0 ||
    !std::isfinite(config.prestream_s) || config.prestream_s <= 1.0 ||
    !std::isfinite(config.ready_timeout_s) || config.ready_timeout_s <= 0.0 ||
    !std::isfinite(config.command_timeout_s) || config.command_timeout_s <= 0.0 ||
    !std::isfinite(config.takeoff_timeout_s) || config.takeoff_timeout_s <= 0.0 ||
    !std::isfinite(config.landing_timeout_s) || config.landing_timeout_s <= 0.0 ||
    !std::isfinite(vio_health_timeout_s_) || vio_health_timeout_s_ <= 0.0 ||
    !std::isfinite(state_timeout_s_) || state_timeout_s_ <= 0.0)
  {
    throw std::invalid_argument("Mission values must be finite/positive and prestream_s must exceed 1 s");
  }

  task_ = std::make_unique<FlightTask>(config);
  state_sub_ = create_subscription<uav_interfaces::msg::VehicleState>(
    "/uav_control/state", 10,
    std::bind(&MissionNode::state_callback, this, std::placeholders::_1));
  if (require_vio_health_) {
    vio_diagnostics_sub_ = create_subscription<diagnostic_msgs::msg::DiagnosticArray>(
      "/uav_bridge/diagnostics", 10,
      std::bind(&MissionNode::vio_diagnostics_callback, this, std::placeholders::_1));
  }
  target_pub_ = create_publisher<geometry_msgs::msg::PoseStamped>(
    "/uav_control/target", 10);
  diagnostics_pub_ = create_publisher<diagnostic_msgs::msg::DiagnosticArray>(
    "/uav_mission/diagnostics", 10);
  command_client_ = create_client<uav_interfaces::srv::FlightCommand>(
    "/uav_control/command");
  cancel_service_ = create_service<std_srvs::srv::Trigger>(
    "/uav_mission/cancel",
    std::bind(
      &MissionNode::cancel_callback, this,
      std::placeholders::_1, std::placeholders::_2));
  timer_ = create_wall_timer(
    std::chrono::milliseconds(50), std::bind(&MissionNode::timer_callback, this));

  RCLCPP_INFO(
    get_logger(), "Mission started: climb %.2f m, stable %.1f s, hover %.1f s",
    config.takeoff_height_m, config.stable_duration_s, config.hover_duration_s);
}

void MissionNode::state_callback(const uav_interfaces::msg::VehicleState::SharedPtr msg)
{
  latest_state_ = *msg;
  state_rx_ = Clock::now();
}

void MissionNode::vio_diagnostics_callback(
  const diagnostic_msgs::msg::DiagnosticArray::SharedPtr msg)
{
  const auto sample = evaluate_vio_diagnostics(
    *msg, now().nanoseconds(), vio_stamp_ns_, vio_health_timeout_s_);
  vio_health_state_ = sample;
  vio_health_ok_ = sample.timestamp_accepted && sample.healthy;
  if (sample.timestamp_accepted) {
    vio_stamp_ns_ = sample.stamp_ns;
    vio_rx_ = Clock::now();
  }
}

void MissionNode::cancel_callback(
  const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
  std::shared_ptr<std_srvs::srv::Trigger::Response> response)
{
  (void)request;
  task_->cancel(Clock::now());
  response->success = true;
  response->message = "Cancellation accepted; task will land and confirm ground/disarmed state";
}

void MissionNode::timer_callback()
{
  const auto now_time = Clock::now();
  const bool stream_fresh = latest_state_ &&
    std::chrono::duration<double>(now_time - state_rx_).count() <= state_timeout_s_;
  const auto * state = latest_state_ ? &*latest_state_ : nullptr;
  const int64_t ros_now_ns = now().nanoseconds();
  const double vio_stamp_age_s = static_cast<double>(ros_now_ns - vio_stamp_ns_) / 1e9;
  const bool vio_receive_fresh = vio_rx_ != Clock::time_point{} &&
    std::chrono::duration<double>(now_time - vio_rx_).count() <= vio_health_timeout_s_;
  const bool vio_fresh = vio_health_ok_ && vio_receive_fresh &&
    vio_stamp_age_s >= -0.1 && vio_stamp_age_s <= vio_health_timeout_s_;
  std::string vio_reason = vio_health_state_.reason;
  if (!vio_receive_fresh && vio_health_state_.timestamp_accepted) {
    vio_reason = "bridge diagnostics receipt is stale";
  } else if (!vio_health_ok_ && vio_reason.empty()) {
    vio_reason = "bridge is not healthy";
  }
  if (vio_reason.empty()) {
    vio_reason = "waiting for bridge diagnostics";
  }
  vio_health_state_.reason = vio_reason;
  const auto result = task_->update(state, stream_fresh, now_time, vio_fresh, vio_reason);

  if (task_->stage_name() != last_logged_stage_) {
    RCLCPP_INFO(get_logger(), "Flight stage: %s", task_->stage_name().c_str());
    last_logged_stage_ = task_->stage_name();
  }
  if (task_->stage_name() == "SAFETY_LAND") {
    RCLCPP_WARN_THROTTLE(
      get_logger(), *get_clock(), 3000,
      "Safety landing active (%s); waiting for fresh landed and disarmed confirmation",
      task_->result_reason().c_str());
  }

  if (result.publish_target) {
    auto target = result.target;
    target.header.stamp = now();
    target_pub_->publish(target);
  }

  if (result.send_command) {
    auto request = std::make_shared<uav_interfaces::srv::FlightCommand::Request>();
    request->command_id = result.command_id;
    request->command = result.command;
    const auto command_id = result.command_id;
    RCLCPP_INFO(
      get_logger(), "Dispatching command id=%u code=%u (dispatch is not state confirmation)",
      command_id, request->command);
    command_client_->async_send_request(
      request, [this, command_id](
        rclcpp::Client<uav_interfaces::srv::FlightCommand>::SharedFuture future)
      {
        try {
          const auto response = future.get();
          RCLCPP_INFO(
            get_logger(), "Command id=%u dispatched=%s: %s", command_id,
            response->dispatched ? "true" : "false", response->message.c_str());
          task_->command_dispatched(
            command_id, response->dispatched, response->message, Clock::now());
          last_dispatched_command_id_ = command_id;
          last_dispatch_known_ = true;
          last_command_dispatched_ = response->dispatched;
          last_dispatch_message_ = response->message;
        } catch (const std::exception & error) {
          RCLCPP_ERROR(get_logger(), "Command id=%u service failed: %s", command_id, error.what());
          last_dispatched_command_id_ = command_id;
          last_dispatch_known_ = false;
          last_command_dispatched_ = false;
          last_dispatch_message_ = error.what();
        }
      });
  }

  publish_diagnostics(stream_fresh, vio_fresh);

  if (result.finished) {
    report_result(result);
    rclcpp::shutdown();
  }
}

void MissionNode::publish_diagnostics(bool state_stream_fresh, bool vio_health_fresh)
{
  diagnostic_msgs::msg::DiagnosticArray message;
  message.header.stamp = now();
  diagnostic_msgs::msg::DiagnosticStatus status;
  status.name = "uav_mission/task";
  status.hardware_id = get_fully_qualified_name();
  status.level = state_stream_fresh && (!require_vio_health_ || vio_health_fresh) ?
    diagnostic_msgs::msg::DiagnosticStatus::OK : diagnostic_msgs::msg::DiagnosticStatus::WARN;
  status.message = task_->stage_name();
  if (!task_->result_reason().empty()) {status.message += ": " + task_->result_reason();}
  if (require_vio_health_ && !vio_health_fresh) {status.message += ": " + vio_health_state_.reason;}
  const auto add = [&status](const std::string & key, const std::string & value) {
      diagnostic_msgs::msg::KeyValue item;
      item.key = key;
      item.value = value;
      status.values.push_back(std::move(item));
    };
  const auto bool_string = [](bool value) {
      return value ? std::string("true") : std::string("false");
    };
  add("contract_version", "1");
  add("stage", task_->stage_name());
  add("reason", task_->result_reason());
  add("finished", bool_string(task_->stage_name() == "FINISHED"));
  add("require_vio_health", bool_string(require_vio_health_));
  add("vio_health_ok", bool_string(vio_health_ok_));
  add("vio_health_fresh", bool_string(vio_health_fresh));
  add("vio_health_reason", vio_health_state_.reason);
  add("vio_backend", vio_health_state_.backend);
  add("vio_enabled", bool_string(vio_health_state_.enabled));
  add("vio_paused", bool_string(vio_health_state_.paused));
  add("vio_pause_reason", vio_health_state_.pause_reason);
  add("vio_visual_fresh", bool_string(vio_health_state_.visual_fresh));
  add("vio_visual_age_s", std::to_string(vio_health_state_.visual_age_s));
  add("vio_input_fresh", bool_string(vio_health_state_.input_fresh));
  add("vio_input_age_s", std::to_string(vio_health_state_.input_age_s));
  add("vio_last_rejection", vio_health_state_.last_rejection);
  add("vio_received", std::to_string(vio_health_state_.received));
  add("vio_adapted", std::to_string(vio_health_state_.adapted));
  add("vio_published", std::to_string(vio_health_state_.published));
  add("vio_rejected", std::to_string(vio_health_state_.rejected));
  add("vio_rate_limited", std::to_string(vio_health_state_.rate_limited));
  add("vio_recovery_visual_count", std::to_string(vio_health_state_.recovery_visual_count));
  add("vio_recovery_odom_count", std::to_string(vio_health_state_.recovery_odom_count));
  add("vio_published_is_px4_receipt", "false");
  add("last_dispatched_command_id", std::to_string(last_dispatched_command_id_));
  add("last_dispatch_known", bool_string(last_dispatch_known_));
  add("last_command_dispatched", bool_string(last_command_dispatched_));
  add("last_dispatch_message", last_dispatch_message_);
  if (latest_state_) {
    const auto & state = *latest_state_;
    add("state_fresh", bool_string(state_stream_fresh));
    add("state_valid", bool_string(state.state_valid && state.connected));
    add("position_valid", bool_string(state.position_valid));
    add("heading_valid", bool_string(state.heading_valid));
    add("velocity_valid", bool_string(state.velocity_valid));
    add("estimator_health_valid", bool_string(state.estimator_health_valid));
    add("estimator_healthy", bool_string(state.estimator_healthy));
    add("failsafe_state_valid", bool_string(state.failsafe_state_valid));
    add("failsafe_active", bool_string(state.failsafe_active));
    add("preflight_check_state_valid", bool_string(state.preflight_check_state_valid));
    add("preflight_checks_passed", bool_string(state.preflight_checks_passed));
    add("control_inhibited", bool_string(state.control_inhibited));
    add("mode", state.mode);
    add("armed", bool_string(state.armed));
    add("landed_state_valid", bool_string(state.landed_state_valid));
    add("landed_state", std::to_string(state.landed_state));
    add("backend_command_id", std::to_string(state.last_command_id));
    add("backend_command_completed", bool_string(state.command_completed));
    add("backend_command_accepted", bool_string(state.command_accepted));
    add("backend_command_message", state.command_message);
  } else {
    add("state_fresh", "false");
  }
  message.status.push_back(std::move(status));
  diagnostics_pub_->publish(message);
}

void MissionNode::report_result(const FlightTask::Output & result)
{
  if (result_reported_) {
    return;
  }
  result_reported_ = true;
  if (result.control_released) {
    RCLCPP_WARN(get_logger(), "STOPPED: %s; landing/disarming not confirmed by this task",
      task_->result_reason().c_str());
    return;
  }
  if (task_->have_hover_measurements()) {
    const auto metrics =
      "hover_max_horizontal_error=" + std::to_string(task_->max_horizontal_error_m()) +
      " m, hover_max_height_error=" + std::to_string(task_->max_vertical_error_m()) +
      " m, hover_max_yaw_error=" + std::to_string(task_->max_yaw_error_rad()) +
      " rad, final_xy_displacement=" +
      std::to_string(task_->final_horizontal_displacement_m()) +
      " m, final_z_from_takeoff=" +
      std::to_string(task_->final_vertical_displacement_m()) + " m";
    if (result.passed) {
      RCLCPP_INFO(
        get_logger(), "PASS: Offboard, arm, takeoff, configured stable hold/hover, "
        "AUTO.LAND handover, landed and disarmed confirmed; %s", metrics.c_str());
    } else if (result.canceled) {
      RCLCPP_WARN(
        get_logger(), "CANCELED: safety landing completed; %s; %s",
        task_->result_reason().c_str(), metrics.c_str());
    } else {
      RCLCPP_ERROR(
        get_logger(), "FAIL: %s; safety landing completed; %s",
        task_->result_reason().c_str(), metrics.c_str());
    }
  } else if (result.passed) {
    RCLCPP_INFO(get_logger(), "PASS: task completed; no hover position measurements were recorded");
  } else if (task_->have_position_measurement()) {
    const auto message =
      "last horizontal target error=" +
      std::to_string(task_->last_horizontal_target_error_m()) +
      " m, last height target error=" +
      std::to_string(task_->last_vertical_target_error_m()) +
      " m, final XY displacement=" +
      std::to_string(task_->final_horizontal_displacement_m()) +
      " m, final height from takeoff=" +
      std::to_string(task_->final_vertical_displacement_m()) + " m";
    if (result.canceled) {
      RCLCPP_WARN(
        get_logger(), "CANCELED: %s; %s", task_->result_reason().c_str(), message.c_str());
    } else {
      RCLCPP_ERROR(
        get_logger(), "FAIL: %s; %s", task_->result_reason().c_str(), message.c_str());
    }
  } else if (result.canceled) {
    RCLCPP_WARN(get_logger(), "CANCELED: %s", task_->result_reason().c_str());
  } else {
    RCLCPP_ERROR(get_logger(), "FAIL: %s; no hover position measurements were recorded",
      task_->result_reason().c_str());
  }
}

}  // namespace uav_mission

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  int result = 0;
  try {
    rclcpp::spin(std::make_shared<uav_mission::MissionNode>());
  } catch (const std::exception & error) {
    RCLCPP_ERROR(rclcpp::get_logger("uav_mission"), "%s", error.what());
    result = 1;
  }
  rclcpp::shutdown();
  return result;
}

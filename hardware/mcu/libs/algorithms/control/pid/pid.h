#ifndef BBF_MCU_LIBS_CONTROL_PID_H
#define BBF_MCU_LIBS_CONTROL_PID_H

/**
 * @file pid.h
 * @brief Discrete positional and incremental PID controllers (pure C99).
 *
 * Includes engineering protections: derivative-on-measurement, optional
 * first-order low-pass filter on the D term, error deadband, feedforward,
 * and conditional-integration anti-windup clamping.
 */

typedef struct {
    float kp;
    float ki;
    float kd;
    float d_filter_tau;  /**< D-term low-pass time constant (s); <= 0 disables */
    float deadband;      /**< Error deadband (>= 0) */
    float out_min;
    float out_max;
    float integral_min;
    float integral_max;
} PidConfig;

typedef struct {
    float integral;
    float prev_error;
    float prev_prev_error;
    float prev_measurement;
    float d_filtered;
    float last_output;
    int initialized;
} PidState;

/** Reset internal controller state to zero. */
void pid_init(PidState *state);

/**
 * @brief Compute one positional PID step.
 *
 * Uses derivative-on-measurement to avoid derivative kick on setpoint steps
 * and conditional integration to prevent integrator windup under saturation.
 */
float pid_update_positional(const PidConfig *cfg, PidState *state,
                            float target, float measurement,
                            float feedforward, float dt);

/**
 * @brief Compute one incremental PID step and return clamped cumulative output.
 */
float pid_update_incremental(const PidConfig *cfg, PidState *state,
                             float target, float measurement, float dt);

#endif /* BBF_MCU_LIBS_CONTROL_PID_H */

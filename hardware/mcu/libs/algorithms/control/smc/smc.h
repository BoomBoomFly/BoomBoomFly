#ifndef BBF_MCU_LIBS_CONTROL_SMC_H
#define BBF_MCU_LIBS_CONTROL_SMC_H

/**
 * @file smc.h
 * @brief 2nd-order Sliding Mode Controller with boundary layer (pure C99).
 *
 * Uses linear sliding surface s = c*e + e_dot and exponential reaching law
 * with continuous saturation sat(s / phi) to attenuate chattering.
 */

typedef struct {
    float c;        /**< Sliding surface slope (> 0) */
    float k;        /**< Exponential reaching gain (>= 0) */
    float epsilon;  /**< Switching gain covering disturbance bound (> 0) */
    float phi;      /**< Boundary layer thickness (> 0 suppresses chattering) */
    float b;        /**< Control effectiveness gain (non-zero) */
    float out_min;
    float out_max;
} SmcConfig;

typedef struct {
    float last_s;  /**< Latest sliding variable value for telemetry/debugging */
} SmcState;

/** Reset SMC state. */
void smc_init(SmcState *state);

/**
 * @brief Compute one 2nd-order SMC control step for x_ddot = f(x, x_dot) + b*u + d.
 */
float smc_update(const SmcConfig *cfg, SmcState *state,
                 float x, float x_dot,
                 float x_d, float x_d_dot, float x_d_ddot,
                 float f_nominal);

#endif /* BBF_MCU_LIBS_CONTROL_SMC_H */

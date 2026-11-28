#ifndef BBF_MCU_LIBS_CONTROL_LADRC_H
#define BBF_MCU_LIBS_CONTROL_LADRC_H

/**
 * @file ladrc.h
 * @brief Bandwidth-parameterized 2nd-order Linear ADRC (LESO + LSEF, pure C99).
 *
 * Estimates total disturbance z3 via a 3rd-order linear extended state observer
 * (LESO) using the actual saturated control output to avoid windup.
 */

typedef struct {
    float b0;       /**< Nominal control gain estimate (must be non-zero) */
    float omega_c;  /**< Controller bandwidth (rad/s) */
    float omega_o;  /**< Observer bandwidth (rad/s), typically 3..5 * omega_c */
    float out_min;
    float out_max;
} LadrcConfig;

typedef struct {
    float z1;          /**< Estimated output y */
    float z2;          /**< Estimated derivative y_dot */
    float z3;          /**< Estimated total disturbance f */
    float last_u_sat;  /**< Previous saturated control input fed back to LESO */
} LadrcState;

/** Initialize observer state with initial output measurement. */
void ladrc_init(LadrcState *state, float init_y);

/**
 * @brief Run one 2nd-order LADRC update step.
 * @param ref     Desired setpoint
 * @param ref_dot Desired setpoint derivative (0 for step reference)
 * @param y       Measured output
 * @param dt      Sample period (s)
 */
float ladrc_update(const LadrcConfig *cfg, LadrcState *state,
                   float ref, float ref_dot, float y, float dt);

#endif /* BBF_MCU_LIBS_CONTROL_LADRC_H */

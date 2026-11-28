#ifndef BBF_MCU_LIBS_CONTROL_EKF_2D_H
#define BBF_MCU_LIBS_CONTROL_EKF_2D_H

/**
 * @file ekf_2d.h
 * @brief 2D planar pose Extended Kalman Filter: state [px, py, yaw]^T (pure C99).
 *
 * Includes angle wrapping into (-pi, pi], Mahalanobis/chi-square outlier
 * gating, and Joseph-form covariance updates to preserve symmetry and
 * positive semi-definiteness in single-precision floating point.
 */

typedef struct {
    float x[3];  /**< State estimate: [px, py, yaw (rad)] */
    float P[9];  /**< 3x3 row-major state covariance matrix */
} Ekf2dState;

/** Wrap an angle in radians into (-pi, pi]. */
float ekf2d_wrap_angle(float angle);

/** Initialize filter state and diagonal covariance from initial variances. */
void ekf2d_init(Ekf2dState *ekf, float px, float py, float yaw,
                const float init_var[3]);

/**
 * @brief Predict step using unicycle kinematics driven by velocity and yaw rate.
 * @param v      Forward linear velocity (m/s)
 * @param omega  Yaw angular velocity (rad/s)
 * @param dt     Time step (s)
 * @param q_diag Process noise variances [q_px, q_py, q_yaw] added per step
 */
void ekf2d_predict(Ekf2dState *ekf, float v, float omega, float dt,
                   const float q_diag[3]);

/**
 * @brief 2D position measurement update with chi-square gating.
 * @param chi2_gate Outlier threshold on gamma = y^T S^-1 y (<= 0 disables gate)
 * @return 1 if accepted and fused, 0 if gated out or singular
 */
int ekf2d_update_pos(Ekf2dState *ekf, float z_px, float z_py,
                     float r_px, float r_py, float chi2_gate);

/**
 * @brief Scalar heading measurement update with angle-wrapped innovation.
 * @param chi2_gate Outlier threshold on gamma = y^2 / S (<= 0 disables gate)
 * @return 1 if accepted and fused, 0 if gated out or singular
 */
int ekf2d_update_yaw(Ekf2dState *ekf, float z_yaw,
                     float r_yaw, float chi2_gate);

#endif /* BBF_MCU_LIBS_CONTROL_EKF_2D_H */

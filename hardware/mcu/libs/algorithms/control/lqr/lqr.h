#ifndef BBF_MCU_LIBS_CONTROL_LQR_H
#define BBF_MCU_LIBS_CONTROL_LQR_H

/**
 * @file lqr.h
 * @brief Discrete LQR state feedback and fixed-size DARE solver (pure C99).
 *
 * Uses row-major matrices and fixed stack buffers (no heap allocation).
 */

#define LQR_MAX_STATE 4
#define LQR_MAX_INPUT 2

/**
 * @brief Online state-feedback control law: u = clamp(u_ref - K * (x - x_ref)).
 *
 * @param n_state Number of states (1..LQR_MAX_STATE)
 * @param n_input Number of inputs (1..LQR_MAX_INPUT)
 * @param K       Feedback gain matrix [n_input x n_state] (row-major)
 * @param x       Current state [n_state]
 * @param x_ref   Reference state [n_state] (NULL treated as zero)
 * @param u_ref   Feedforward input [n_input] (NULL treated as zero)
 * @param u_min   Lower input bounds [n_input] (NULL disables lower clamp)
 * @param u_max   Upper input bounds [n_input] (NULL disables upper clamp)
 * @param u_out   Computed control output [n_input]
 */
void lqr_compute(int n_state, int n_input, const float *K,
                 const float *x, const float *x_ref, const float *u_ref,
                 const float *u_min, const float *u_max, float *u_out);

/**
 * @brief Solve the Discrete Algebraic Riccati Equation (DARE) by iteration.
 *
 * @param n_state  State dimension (1..LQR_MAX_STATE)
 * @param n_input  Input dimension (1..LQR_MAX_INPUT)
 * @param Ad       Discrete state matrix [n_state x n_state]
 * @param Bd       Discrete input matrix [n_state x n_input]
 * @param Q        Symmetric state cost matrix [n_state x n_state]
 * @param R        Positive-definite input cost matrix [n_input x n_input]
 * @param max_iter Maximum Riccati iterations
 * @param tol      Convergence tolerance on max elementwise delta of P
 * @param K_out    Output optimal gain matrix [n_input x n_state]
 * @return 0 on convergence, -1 on invalid args / singular matrix / non-convergence
 */
int lqr_solve_dare(int n_state, int n_input,
                   const float *Ad, const float *Bd,
                   const float *Q, const float *R,
                   int max_iter, float tol, float *K_out);

#endif /* BBF_MCU_LIBS_CONTROL_LQR_H */

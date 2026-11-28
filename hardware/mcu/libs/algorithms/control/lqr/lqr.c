#include "lqr.h"

#include <math.h>
#include <stddef.h>

static void mat_mul(int rows, int inner, int cols,
                    const float *A, const float *B, float *C)
{
    int i;
    int j;
    int k;

    for (i = 0; i < rows; ++i) {
        for (j = 0; j < cols; ++j) {
            float sum = 0.0f;
            for (k = 0; k < inner; ++k) {
                sum += A[i * inner + k] * B[k * cols + j];
            }
            C[i * cols + j] = sum;
        }
    }
}

static void mat_mul_at_b(int rows_a, int cols_a, int cols_b,
                         const float *A, const float *B, float *C)
{
    int i;
    int j;
    int k;

    for (i = 0; i < cols_a; ++i) {
        for (j = 0; j < cols_b; ++j) {
            float sum = 0.0f;
            for (k = 0; k < rows_a; ++k) {
                sum += A[k * cols_a + i] * B[k * cols_b + j];
            }
            C[i * cols_b + j] = sum;
        }
    }
}

static int invert_small_sym(int m, const float *S, float *S_inv)
{
    if (m == 1) {
        if (fabsf(S[0]) < 1e-12f) {
            return -1;
        }
        S_inv[0] = 1.0f / S[0];
        return 0;
    }
    if (m == 2) {
        float det = S[0] * S[3] - S[1] * S[2];
        float inv_det;
        if (fabsf(det) < 1e-12f) {
            return -1;
        }
        inv_det = 1.0f / det;
        S_inv[0] = S[3] * inv_det;
        S_inv[1] = -S[1] * inv_det;
        S_inv[2] = -S[2] * inv_det;
        S_inv[3] = S[0] * inv_det;
        return 0;
    }
    return -1;
}

void lqr_compute(int n_state, int n_input, const float *K,
                 const float *x, const float *x_ref, const float *u_ref,
                 const float *u_min, const float *u_max, float *u_out)
{
    int i;
    int j;

    if (K == NULL || x == NULL || u_out == NULL ||
        n_state <= 0 || n_state > LQR_MAX_STATE ||
        n_input <= 0 || n_input > LQR_MAX_INPUT) {
        return;
    }

    for (i = 0; i < n_input; ++i) {
        float u = (u_ref != NULL) ? u_ref[i] : 0.0f;
        for (j = 0; j < n_state; ++j) {
            float err = x[j] - ((x_ref != NULL) ? x_ref[j] : 0.0f);
            u -= K[i * n_state + j] * err;
        }
        if (u_min != NULL && u < u_min[i]) {
            u = u_min[i];
        }
        if (u_max != NULL && u > u_max[i]) {
            u = u_max[i];
        }
        u_out[i] = u;
    }
}

int lqr_solve_dare(int n_state, int n_input,
                   const float *Ad, const float *Bd,
                   const float *Q, const float *R,
                   int max_iter, float tol, float *K_out)
{
    float P[LQR_MAX_STATE * LQR_MAX_STATE];
    float PA[LQR_MAX_STATE * LQR_MAX_STATE];
    float PB[LQR_MAX_STATE * LQR_MAX_INPUT];
    float S[LQR_MAX_INPUT * LQR_MAX_INPUT];
    float S_inv[LQR_MAX_INPUT * LQR_MAX_INPUT];
    float BtPA[LQR_MAX_INPUT * LQR_MAX_STATE];
    float K[LQR_MAX_INPUT * LQR_MAX_STATE];
    float AtPA[LQR_MAX_STATE * LQR_MAX_STATE];
    float corr[LQR_MAX_STATE * LQR_MAX_STATE];
    float P_next[LQR_MAX_STATE * LQR_MAX_STATE];
    int iter;
    int i;
    int j;

    if (n_state <= 0 || n_state > LQR_MAX_STATE ||
        n_input <= 0 || n_input > LQR_MAX_INPUT ||
        Ad == NULL || Bd == NULL || Q == NULL || R == NULL || K_out == NULL ||
        max_iter <= 0 || tol <= 0.0f) {
        return -1;
    }

    for (i = 0; i < n_state * n_state; ++i) {
        P[i] = Q[i];
    }

    for (iter = 0; iter < max_iter; ++iter) {
        float max_diff = 0.0f;

        mat_mul(n_state, n_state, n_state, P, Ad, PA);
        mat_mul(n_state, n_state, n_input, P, Bd, PB);

        /* S = R + Bd^T * P * Bd */
        mat_mul_at_b(n_state, n_input, n_input, Bd, PB, S);
        for (i = 0; i < n_input * n_input; ++i) {
            S[i] += R[i];
        }
        if (invert_small_sym(n_input, S, S_inv) != 0) {
            return -1;
        }

        /* K = S^-1 * (Bd^T * P * Ad) */
        mat_mul_at_b(n_state, n_input, n_state, Bd, PA, BtPA);
        mat_mul(n_input, n_input, n_state, S_inv, BtPA, K);

        /* P_next = Ad^T * P * Ad - (Bd^T * P * Ad)^T * K + Q */
        mat_mul_at_b(n_state, n_state, n_state, Ad, PA, AtPA);
        mat_mul_at_b(n_input, n_state, n_state, BtPA, K, corr);

        for (i = 0; i < n_state; ++i) {
            for (j = 0; j < n_state; ++j) {
                int idx = i * n_state + j;
                P_next[idx] = AtPA[idx] - corr[idx] + Q[idx];
            }
        }

        /* Symmetrize to preserve numerical stability across iterations. */
        for (i = 0; i < n_state; ++i) {
            for (j = i; j < n_state; ++j) {
                int ij = i * n_state + j;
                int ji = j * n_state + i;
                float avg = 0.5f * (P_next[ij] + P_next[ji]);
                float diff = fabsf(avg - P[ij]);
                P_next[ij] = avg;
                P_next[ji] = avg;
                if (diff > max_diff) {
                    max_diff = diff;
                }
            }
        }

        for (i = 0; i < n_state * n_state; ++i) {
            P[i] = P_next[i];
        }

        if (max_diff < tol) {
            for (i = 0; i < n_input * n_state; ++i) {
                K_out[i] = K[i];
            }
            return 0;
        }
    }

    return -1;
}

#include "ekf_2d.h"

#include <math.h>
#include <stddef.h>
#include <string.h>

#define EKF2D_PI 3.14159265358979323846f
#define EKF2D_TWO_PI 6.28318530717958647692f

static void mat3_mul(const float A[9], const float B[9], float C[9])
{
    int i;
    int j;
    int k;

    for (i = 0; i < 3; ++i) {
        for (j = 0; j < 3; ++j) {
            float sum = 0.0f;
            for (k = 0; k < 3; ++k) {
                sum += A[i * 3 + k] * B[k * 3 + j];
            }
            C[i * 3 + j] = sum;
        }
    }
}

static void symmetrize_3x3(float P[9])
{
    int i;
    int j;

    for (i = 0; i < 3; ++i) {
        for (j = i + 1; j < 3; ++j) {
            float avg = 0.5f * (P[i * 3 + j] + P[j * 3 + i]);
            P[i * 3 + j] = avg;
            P[j * 3 + i] = avg;
        }
    }
}

static void joseph_update(float P[9], const float I_KH[9], const float KRKt[9])
{
    float temp[9];
    int i;
    int j;
    int k;

    mat3_mul(I_KH, P, temp);
    for (i = 0; i < 3; ++i) {
        for (j = 0; j < 3; ++j) {
            float sum = KRKt[i * 3 + j];
            for (k = 0; k < 3; ++k) {
                sum += temp[i * 3 + k] * I_KH[j * 3 + k];
            }
            P[i * 3 + j] = sum;
        }
    }
    symmetrize_3x3(P);
}

float ekf2d_wrap_angle(float angle)
{
    while (angle > EKF2D_PI) {
        angle -= EKF2D_TWO_PI;
    }
    while (angle <= -EKF2D_PI) {
        angle += EKF2D_TWO_PI;
    }
    return angle;
}

void ekf2d_init(Ekf2dState *ekf, float px, float py, float yaw,
                const float init_var[3])
{
    if (ekf == NULL) {
        return;
    }
    memset(ekf, 0, sizeof(*ekf));
    ekf->x[0] = px;
    ekf->x[1] = py;
    ekf->x[2] = ekf2d_wrap_angle(yaw);
    if (init_var != NULL) {
        ekf->P[0] = init_var[0];
        ekf->P[4] = init_var[1];
        ekf->P[8] = init_var[2];
    }
}

void ekf2d_predict(Ekf2dState *ekf, float v, float omega, float dt,
                   const float q_diag[3])
{
    float theta;
    float c;
    float s;
    float F[9];
    float FP[9];
    int i;
    int j;
    int k;

    if (ekf == NULL || dt <= 0.0f) {
        return;
    }

    theta = ekf->x[2];
    c = cosf(theta);
    s = sinf(theta);

    ekf->x[0] += v * c * dt;
    ekf->x[1] += v * s * dt;
    ekf->x[2] = ekf2d_wrap_angle(theta + omega * dt);

    F[0] = 1.0f; F[1] = 0.0f; F[2] = -v * s * dt;
    F[3] = 0.0f; F[4] = 1.0f; F[5] =  v * c * dt;
    F[6] = 0.0f; F[7] = 0.0f; F[8] = 1.0f;

    mat3_mul(F, ekf->P, FP);
    for (i = 0; i < 3; ++i) {
        for (j = 0; j < 3; ++j) {
            float sum = 0.0f;
            for (k = 0; k < 3; ++k) {
                sum += FP[i * 3 + k] * F[j * 3 + k];
            }
            ekf->P[i * 3 + j] = sum;
        }
    }

    if (q_diag != NULL) {
        ekf->P[0] += q_diag[0];
        ekf->P[4] += q_diag[1];
        ekf->P[8] += q_diag[2];
    }
    symmetrize_3x3(ekf->P);
}

int ekf2d_update_pos(Ekf2dState *ekf, float z_px, float z_py,
                     float r_px, float r_py, float chi2_gate)
{
    float y0;
    float y1;
    float s00;
    float s01;
    float s10;
    float s11;
    float det;
    float inv_det;
    float si00;
    float si01;
    float si10;
    float si11;
    float gamma;
    float K[6];
    float I_KH[9];
    float KRKt[9];
    int i;
    int j;

    if (ekf == NULL) {
        return 0;
    }

    y0 = z_px - ekf->x[0];
    y1 = z_py - ekf->x[1];

    s00 = ekf->P[0] + r_px;
    s01 = ekf->P[1];
    s10 = ekf->P[3];
    s11 = ekf->P[4] + r_py;

    det = s00 * s11 - s01 * s10;
    if (det <= 1e-12f) {
        return 0;
    }
    inv_det = 1.0f / det;
    si00 = s11 * inv_det;
    si01 = -s01 * inv_det;
    si10 = -s10 * inv_det;
    si11 = s00 * inv_det;

    gamma = y0 * (si00 * y0 + si01 * y1) + y1 * (si10 * y0 + si11 * y1);
    if (chi2_gate > 0.0f && gamma > chi2_gate) {
        return 0;
    }

    for (i = 0; i < 3; ++i) {
        float p0 = ekf->P[i * 3 + 0];
        float p1 = ekf->P[i * 3 + 1];
        K[i * 2 + 0] = p0 * si00 + p1 * si10;
        K[i * 2 + 1] = p0 * si01 + p1 * si11;
    }

    ekf->x[0] += K[0] * y0 + K[1] * y1;
    ekf->x[1] += K[2] * y0 + K[3] * y1;
    ekf->x[2] = ekf2d_wrap_angle(ekf->x[2] + K[4] * y0 + K[5] * y1);

    /* Joseph form: P = (I - K*H)*P*(I - K*H)^T + K*R*K^T */
    I_KH[0] = 1.0f - K[0]; I_KH[1] = -K[1];        I_KH[2] = 0.0f;
    I_KH[3] = -K[2];        I_KH[4] = 1.0f - K[3]; I_KH[5] = 0.0f;
    I_KH[6] = -K[4];        I_KH[7] = -K[5];        I_KH[8] = 1.0f;

    for (i = 0; i < 3; ++i) {
        for (j = 0; j < 3; ++j) {
            KRKt[i * 3 + j] = K[i * 2 + 0] * r_px * K[j * 2 + 0]
                            + K[i * 2 + 1] * r_py * K[j * 2 + 1];
        }
    }
    joseph_update(ekf->P, I_KH, KRKt);
    return 1;
}

int ekf2d_update_yaw(Ekf2dState *ekf, float z_yaw,
                     float r_yaw, float chi2_gate)
{
    float y;
    float s;
    float gamma;
    float K[3];
    float I_KH[9];
    float KRKt[9];
    int i;
    int j;

    if (ekf == NULL) {
        return 0;
    }

    y = ekf2d_wrap_angle(z_yaw - ekf->x[2]);
    s = ekf->P[8] + r_yaw;
    if (s <= 1e-12f) {
        return 0;
    }

    gamma = (y * y) / s;
    if (chi2_gate > 0.0f && gamma > chi2_gate) {
        return 0;
    }

    K[0] = ekf->P[2] / s;
    K[1] = ekf->P[5] / s;
    K[2] = ekf->P[8] / s;

    ekf->x[0] += K[0] * y;
    ekf->x[1] += K[1] * y;
    ekf->x[2] = ekf2d_wrap_angle(ekf->x[2] + K[2] * y);

    I_KH[0] = 1.0f; I_KH[1] = 0.0f; I_KH[2] = -K[0];
    I_KH[3] = 0.0f; I_KH[4] = 1.0f; I_KH[5] = -K[1];
    I_KH[6] = 0.0f; I_KH[7] = 0.0f; I_KH[8] = 1.0f - K[2];

    for (i = 0; i < 3; ++i) {
        for (j = 0; j < 3; ++j) {
            KRKt[i * 3 + j] = K[i] * r_yaw * K[j];
        }
    }
    joseph_update(ekf->P, I_KH, KRKt);
    return 1;
}

#include "estimation/ekf_2d/ekf_2d.h"
#include "control/ladrc/ladrc.h"
#include "control/lqr/lqr.h"
#include "control/pid/pid.h"
#include "control/smc/smc.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>

static void test_pid(void)
{
    PidConfig pos_cfg = {
        6.0f, 4.0f, 0.2f,
        0.02f, 0.0f,
        -10.0f, 10.0f,
        -10.0f, 10.0f
    };
    PidState state;
    float y = 0.0f;
    float dt = 0.01f;
    int i;

    pid_init(&state);
    for (i = 0; i < 800; ++i) {
        float u = pid_update_positional(&pos_cfg, &state, 2.0f, y, 0.0f, dt);
        assert(u >= pos_cfg.out_min && u <= pos_cfg.out_max);
        y += (-y + u - 0.5f) * dt;
    }
    assert(fabsf(y - 2.0f) < 1e-2f);

    {
        float y_pos = y;
        PidConfig inc_cfg = {
            4.0f, 6.0f, 0.02f,
            0.0f, 0.0f,
            -10.0f, 10.0f,
            -10.0f, 10.0f
        };
        pid_init(&state);
        y = 0.0f;
        for (i = 0; i < 1000; ++i) {
            float u = pid_update_incremental(&inc_cfg, &state, 2.0f, y, dt);
            assert(u >= inc_cfg.out_min && u <= inc_cfg.out_max);
            y += (-y + u - 0.5f) * dt;
        }
        assert(fabsf(y - 2.0f) < 1e-2f);
        printf("[PASS] PID (positional=%.4f, incremental=%.4f)\n", y_pos, y);
    }
}

static void test_ladrc(void)
{
    LadrcConfig cfg = {
        2.0f,   /* b0 */
        6.0f,   /* omega_c */
        24.0f,  /* omega_o */
        -15.0f, 15.0f
    };
    LadrcState state;
    float y = 0.0f;
    float y_dot = 0.0f;
    float dt = 0.002f;
    float disturbance = 3.0f;
    int i;

    ladrc_init(&state, y);
    for (i = 0; i < 2500; ++i) {
        float u = ladrc_update(&cfg, &state, 1.5f, 0.0f, y, dt);
        float y_ddot = 2.0f * u + disturbance;
        y_dot += y_ddot * dt;
        y += y_dot * dt;
    }
    assert(fabsf(y - 1.5f) < 0.05f);
    assert(fabsf(state.z3 - disturbance) < 0.2f);
    printf("[PASS] LADRC: final y=%.4f, z3=%.4f (true d=%.2f)\n",
           y, state.z3, disturbance);
}

static void test_lqr(void)
{
    float dt = 0.02f;
    float Ad[4] = {
        1.0f, dt,
        0.0f, 1.0f
    };
    float Bd[2] = {
        0.5f * dt * dt,
        dt
    };
    float Q[4] = {
        10.0f, 0.0f,
        0.0f, 1.0f
    };
    float R[1] = {0.1f};
    float K[2] = {0.0f, 0.0f};
    float x[2] = {0.0f, 0.0f};
    float x_ref[2] = {1.0f, 0.0f};
    float u_min[1] = {-5.0f};
    float u_max[1] = {5.0f};
    int ret;
    int i;

    ret = lqr_solve_dare(2, 1, Ad, Bd, Q, R, 500, 1e-6f, K);
    assert(ret == 0);

    for (i = 0; i < 300; ++i) {
        float u[1];
        float x0_next;
        float x1_next;
        lqr_compute(2, 1, K, x, x_ref, NULL, u_min, u_max, u);
        x0_next = Ad[0] * x[0] + Ad[1] * x[1] + Bd[0] * u[0];
        x1_next = Ad[2] * x[0] + Ad[3] * x[1] + Bd[1] * u[0];
        x[0] = x0_next;
        x[1] = x1_next;
    }
    assert(fabsf(x[0] - 1.0f) < 0.02f);
    assert(fabsf(x[1]) < 0.02f);
    printf("[PASS] LQR: K=[%.3f, %.3f], final x=[%.4f, %.4f]\n",
           K[0], K[1], x[0], x[1]);
}

static void test_smc(void)
{
    SmcConfig cfg = {
        5.0f,   /* c */
        8.0f,   /* k */
        3.0f,   /* epsilon */
        0.05f,  /* phi */
        1.0f,   /* b */
        -20.0f, 20.0f
    };
    SmcState state;
    float x = 0.5f;
    float x_dot = 0.0f;
    float dt = 0.001f;
    float max_tail_err = 0.0f;
    int i;

    smc_init(&state);
    for (i = 0; i < 5000; ++i) {
        float t = (float)i * dt;
        float x_d = sinf(t);
        float x_d_dot = cosf(t);
        float x_d_ddot = -sinf(t);
        float f_nom = -0.5f * x_dot;
        float disturbance = 1.2f * sinf(2.0f * t) + 0.8f;
        float u = smc_update(&cfg, &state, x, x_dot,
                             x_d, x_d_dot, x_d_ddot, f_nom);
        float x_ddot = f_nom + cfg.b * u + disturbance;
        x_dot += x_ddot * dt;
        x += x_dot * dt;
        if (i >= 3000) {
            float err = fabsf(x - x_d);
            if (err > max_tail_err) {
                max_tail_err = err;
            }
        }
    }
    assert(max_tail_err < 0.05f);
    printf("[PASS] SMC: max steady tracking error=%.4f\n", max_tail_err);
}

static void test_ekf2d(void)
{
    Ekf2dState ekf;
    float init_var[3] = {0.1f, 0.1f, 0.05f};
    float q_diag[3] = {1e-3f, 1e-3f, 1e-3f};
    float dt = 0.02f;
    float tx = 0.0f;
    float ty = 0.0f;
    float tyaw = 2.8f;
    float dr_x = 0.0f;
    float dr_y = 0.0f;
    float dr_yaw = 2.8f;
    int outlier_ret = -1;
    int i;

    ekf2d_init(&ekf, tx, ty, tyaw, init_var);

    for (i = 1; i <= 300; ++i) {
        float v_true = 1.0f;
        float w_true = 0.3f;
        float v_odom = 1.08f;
        float w_odom = 0.34f;

        tx += v_true * cosf(tyaw) * dt;
        ty += v_true * sinf(tyaw) * dt;
        tyaw = ekf2d_wrap_angle(tyaw + w_true * dt);

        dr_x += v_odom * cosf(dr_yaw) * dt;
        dr_y += v_odom * sinf(dr_yaw) * dt;
        dr_yaw = ekf2d_wrap_angle(dr_yaw + w_odom * dt);

        ekf2d_predict(&ekf, v_odom, w_odom, dt, q_diag);

        if (i == 150) {
            outlier_ret = ekf2d_update_pos(&ekf, tx + 10.0f, ty - 10.0f,
                                           0.02f, 0.02f, 9.21f);
            assert(outlier_ret == 0);
        }

        if (i % 5 == 0) {
            int ok_pos = ekf2d_update_pos(&ekf, tx, ty, 0.02f, 0.02f, 9.21f);
            int ok_yaw = ekf2d_update_yaw(&ekf, tyaw, 0.01f, 6.63f);
            assert(ok_pos == 1);
            assert(ok_yaw == 1);
        }
    }

    {
        float ekf_pos_err = hypotf(ekf.x[0] - tx, ekf.x[1] - ty);
        float dr_pos_err = hypotf(dr_x - tx, dr_y - ty);
        float yaw_err = fabsf(ekf2d_wrap_angle(ekf.x[2] - tyaw));
        assert(outlier_ret == 0);
        assert(ekf_pos_err < 0.15f);
        assert(yaw_err < 0.05f);
        assert(ekf_pos_err < 0.25f * dr_pos_err);
        printf("[PASS] EKF2D: pos_err=%.4f m (DR=%.4f m), yaw_err=%.4f rad\n",
               ekf_pos_err, dr_pos_err, yaw_err);
    }
}

int main(void)
{
    test_pid();
    test_ladrc();
    test_lqr();
    test_smc();
    test_ekf2d();
    printf("All 5 control/estimation reference tests passed.\n");
    return 0;
}

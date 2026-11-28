#include "ladrc.h"

#include <stddef.h>

static float clampf(float value, float min_val, float max_val)
{
    if (value < min_val) {
        return min_val;
    }
    if (value > max_val) {
        return max_val;
    }
    return value;
}

void ladrc_init(LadrcState *state, float init_y)
{
    if (state == NULL) {
        return;
    }
    state->z1 = init_y;
    state->z2 = 0.0f;
    state->z3 = 0.0f;
    state->last_u_sat = 0.0f;
}

float ladrc_update(const LadrcConfig *cfg, LadrcState *state,
                   float ref, float ref_dot, float y, float dt)
{
    float wo;
    float wc;
    float beta1;
    float beta2;
    float beta3;
    float obs_err;
    float z1_dot;
    float z2_dot;
    float z3_dot;
    float kp;
    float kd;
    float u0;
    float u_sat;

    if (cfg == NULL || state == NULL) {
        return 0.0f;
    }
    if (dt <= 0.0f || cfg->b0 == 0.0f) {
        return state->last_u_sat;
    }

    wo = cfg->omega_o;
    wc = cfg->omega_c;

    /* Poles placed at -omega_o for 3rd-order LESO. */
    beta1 = 3.0f * wo;
    beta2 = 3.0f * wo * wo;
    beta3 = wo * wo * wo;

    obs_err = state->z1 - y;
    z1_dot = state->z2 - beta1 * obs_err;
    z2_dot = state->z3 - beta2 * obs_err + cfg->b0 * state->last_u_sat;
    z3_dot = -beta3 * obs_err;

    state->z1 += z1_dot * dt;
    state->z2 += z2_dot * dt;
    state->z3 += z3_dot * dt;

    /* Poles placed at -omega_c for PD state-error feedback. */
    kp = wc * wc;
    kd = 2.0f * wc;
    u0 = kp * (ref - state->z1) + kd * (ref_dot - state->z2);

    u_sat = clampf((u0 - state->z3) / cfg->b0, cfg->out_min, cfg->out_max);
    state->last_u_sat = u_sat;
    return u_sat;
}

#include "smc.h"

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

void smc_init(SmcState *state)
{
    if (state == NULL) {
        return;
    }
    state->last_s = 0.0f;
}

float smc_update(const SmcConfig *cfg, SmcState *state,
                 float x, float x_dot,
                 float x_d, float x_d_dot, float x_d_ddot,
                 float f_nominal)
{
    float e;
    float e_dot;
    float s;
    float sat_s;
    float u;

    if (cfg == NULL || state == NULL || cfg->b == 0.0f) {
        return 0.0f;
    }

    e = x - x_d;
    e_dot = x_dot - x_d_dot;
    s = cfg->c * e + e_dot;
    state->last_s = s;

    /* Boundary layer replaces sign(s) with continuous sat(s / phi). */
    if (cfg->phi > 0.0f) {
        sat_s = clampf(s / cfg->phi, -1.0f, 1.0f);
    } else if (s > 0.0f) {
        sat_s = 1.0f;
    } else if (s < 0.0f) {
        sat_s = -1.0f;
    } else {
        sat_s = 0.0f;
    }

    u = (x_d_ddot - f_nominal - cfg->c * e_dot - cfg->k * s - cfg->epsilon * sat_s) / cfg->b;
    return clampf(u, cfg->out_min, cfg->out_max);
}

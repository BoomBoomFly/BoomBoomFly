#include "pid.h"

#include <math.h>
#include <stddef.h>
#include <string.h>

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

void pid_init(PidState *state)
{
    if (state == NULL) {
        return;
    }
    memset(state, 0, sizeof(*state));
}

float pid_update_positional(const PidConfig *cfg, PidState *state,
                            float target, float measurement,
                            float feedforward, float dt)
{
    float error;
    float p_term;
    float d_raw;
    float i_candidate;
    float u_unsat;
    float u_out;

    if (cfg == NULL || state == NULL) {
        return 0.0f;
    }
    if (dt <= 0.0f) {
        return state->last_output;
    }

    error = target - measurement;
    if (cfg->deadband > 0.0f && fabsf(error) < cfg->deadband) {
        error = 0.0f;
    }

    if (!state->initialized) {
        state->prev_measurement = measurement;
        state->prev_error = error;
        state->prev_prev_error = error;
        state->d_filtered = 0.0f;
        state->initialized = 1;
    }

    p_term = cfg->kp * error;

    /* Derivative on measurement prevents step-change spikes from target jumps. */
    d_raw = -cfg->kd * (measurement - state->prev_measurement) / dt;
    if (cfg->d_filter_tau > 0.0f) {
        float alpha = dt / (cfg->d_filter_tau + dt);
        state->d_filtered += alpha * (d_raw - state->d_filtered);
    } else {
        state->d_filtered = d_raw;
    }

    i_candidate = clampf(state->integral + cfg->ki * error * dt,
                         cfg->integral_min, cfg->integral_max);
    u_unsat = feedforward + p_term + i_candidate + state->d_filtered;

    /* Conditional integration: pause windup when saturated in error direction. */
    if (!((u_unsat > cfg->out_max && error > 0.0f) ||
          (u_unsat < cfg->out_min && error < 0.0f))) {
        state->integral = i_candidate;
    }

    u_out = clampf(feedforward + p_term + state->integral + state->d_filtered,
                   cfg->out_min, cfg->out_max);

    state->prev_measurement = measurement;
    state->prev_error = error;
    state->last_output = u_out;
    return u_out;
}

float pid_update_incremental(const PidConfig *cfg, PidState *state,
                             float target, float measurement, float dt)
{
    float error;
    float du;
    float u_out;

    if (cfg == NULL || state == NULL) {
        return 0.0f;
    }
    if (dt <= 0.0f) {
        return state->last_output;
    }

    error = target - measurement;
    if (cfg->deadband > 0.0f && fabsf(error) < cfg->deadband) {
        error = 0.0f;
    }

    if (!state->initialized) {
        state->prev_measurement = measurement;
        state->initialized = 1;
    }

    du = cfg->kp * (error - state->prev_error)
       + cfg->ki * dt * error
       + (cfg->kd / dt) * (error - 2.0f * state->prev_error + state->prev_prev_error);

    u_out = clampf(state->last_output + du, cfg->out_min, cfg->out_max);

    state->prev_prev_error = state->prev_error;
    state->prev_error = error;
    state->prev_measurement = measurement;
    state->last_output = u_out;
    return u_out;
}

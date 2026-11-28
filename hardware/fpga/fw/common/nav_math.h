#ifndef NAV_MATH_H
#define NAV_MATH_H

#include <stdint.h>

static inline int32_t abs32(int32_t value)
{
    return value < 0 ? -value : value;
}

static inline int64_t abs64(int64_t value)
{
    return value < 0 ? -value : value;
}

static inline uint64_t ceil_div(uint64_t numerator, uint64_t denominator)
{
    return numerator / denominator + (numerator % denominator != 0);
}

#endif

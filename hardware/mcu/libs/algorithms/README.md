# MCU 算法库（`libs/algorithms`）

本目录集中存放与芯片和 HAL 解耦的纯 C99 控制、状态估计与信号滤波算法，按独立子目录存放各算法模块，均采用零堆分配（无 `malloc`）与单精度 `float` 运算。

## 目录结构

| 子目录 | 模块 | 文件 | 对应要点 |
| --- | --- | --- | --- |
| `control/pid/` | **PID** | [`pid.h`](control/pid/pid.h) / [`pid.c`](control/pid/pid.c) | 位置式（微分先行、一阶低通、死区、前馈、条件积分抗饱和）与增量式 PID |
| `control/ladrc/` | **LADRC** | [`ladrc.h`](control/ladrc/ladrc.h) / [`ladrc.c`](control/ladrc/ladrc.c) | 二阶线性自抗扰（3 阶 LESO + PD LSEF），带宽参数化（$b_0, \omega_c, \omega_o$）与限幅防饱和 |
| `control/lqr/` | **LQR** | [`lqr.h`](control/lqr/lqr.h) / [`lqr.c`](control/lqr/lqr.c) | 离散状态反馈 `lqr_compute` 与固定栈内存 DARE 求解器 `lqr_solve_dare`（$n \le 4, m \le 2$） |
| `control/smc/` | **SMC** | [`smc.h`](control/smc/smc.h) / [`smc.c`](control/smc/smc.c) | 二阶线性滑模面 + 指数趋近律，连续饱和边界层 $\operatorname{sat}(s/\Phi)$ 抑制抖振 |
| `estimation/ekf_2d/` | **2D EKF** | [`ekf_2d.h`](estimation/ekf_2d/ekf_2d.h) / [`ekf_2d.c`](estimation/ekf_2d/ekf_2d.c) | 平面位姿 $[p_x, p_y, \psi]^T$ 滤波，包含航向回绕、卡方门控与 Joseph 形式协方差更新 |
| `filter/` | *预留* | — | 后续按需放置巴特沃斯低通、陷波滤波等数字滤波器 |

## 主机闭环仿真验证（示例）

[`examples/demo_algorithms.c`](examples/demo_algorithms.c) 对控制与状态估计模块做了闭环仿真与数值断言，在 Linux / WSL 下可直接编译运行：

```bash
gcc -std=c99 -O2 -Wall -Wextra -Wpedantic -Ihardware/mcu/libs/algorithms \
  hardware/mcu/libs/algorithms/control/pid/pid.c \
  hardware/mcu/libs/algorithms/control/ladrc/ladrc.c \
  hardware/mcu/libs/algorithms/control/lqr/lqr.c \
  hardware/mcu/libs/algorithms/control/smc/smc.c \
  hardware/mcu/libs/algorithms/estimation/ekf_2d/ekf_2d.c \
  hardware/mcu/libs/algorithms/examples/demo_algorithms.c \
  -lm -o /tmp/demo_algorithms && /tmp/demo_algorithms && rm -f /tmp/demo_algorithms
```

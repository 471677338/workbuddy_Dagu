/**
 * @file motor_control.c
 * @brief 基于 DRV8301 的三相无刷电机 FOC + SVPWM 控制实现
 */

#include "motor_control.h"

/* ============================================================
 *  PI 控制器
 * ============================================================ */

void PID_SetParams(PID_t *pid, float kp, float ki, float out_min, float out_max)
{
    pid->kp        = kp;
    pid->ki        = ki;
    pid->integrator = 0.0f;
    pid->out_min   = out_min;
    pid->out_max   = out_max;
}

void PID_Reset(PID_t *pid)
{
    pid->integrator = 0.0f;
}

/**
 * @brief PI计算（位置式，积分抗饱和）
 * @param pid   PI控制器结构
 * @param error 误差 = 给定 - 反馈
 * @retval 控制输出
 */
float PID_Calc(PID_t *pid, float error)
{
    float p_out = pid->kp * error;
    float i_out = pid->integrator + pid->ki * error;

    /* 积分抗饱和：先将输出夹到限幅范围再更新积分 */
    float out = p_out + i_out;
    if (out > pid->out_max) {
        out = pid->out_max;
        /* 防止积分继续增大（条件积分）*/
        if (error > 0.0f) i_out = pid->out_max - p_out;
    } else if (out < pid->out_min) {
        out = pid->out_min;
        if (error < 0.0f) i_out = pid->out_min - p_out;
    }
    pid->integrator = i_out;

    return out;
}

/* ============================================================
 *  Clarke / Park 变换
 * ============================================================ */

/**
 * @brief Clarke 变换（假设三相平衡：ia+ib+ic=0）
 *   α = ia
 *   β = (ia + 2*ib) / sqrt(3)
 */
AlphaBeta_t Motor_Clarke(float ia, float ib, float ic)
{
    (void)ic;  /* 三相平衡时 ic = -(ia+ib)，不需要独立计算 */
    AlphaBeta_t result;
    result.alpha = ia;
    result.beta  = (ia + 2.0f * ib) * ONE_OVER_SQRT3;
    return result;
}

/**
 * @brief Park 变换
 *   d =  α*cos(θ) + β*sin(θ)
 *   q = -α*sin(θ) + β*cos(θ)
 */
DQ_t Motor_Park(AlphaBeta_t iab, float theta)
{
    float sin_t = sinf(theta);
    float cos_t = cosf(theta);
    DQ_t result;
    result.d =  iab.alpha * cos_t + iab.beta * sin_t;
    result.q = -iab.alpha * sin_t + iab.beta * cos_t;
    return result;
}

/**
 * @brief 逆 Park 变换
 *   α = d*cos(θ) - q*sin(θ)
 *   β = d*sin(θ) + q*cos(θ)
 */
AlphaBeta_t Motor_InvPark(DQ_t vdq, float theta)
{
    float sin_t = sinf(theta);
    float cos_t = cosf(theta);
    AlphaBeta_t result;
    result.alpha = vdq.d * cos_t - vdq.q * sin_t;
    result.beta  = vdq.d * sin_t + vdq.q * cos_t;
    return result;
}

/* ============================================================
 *  SVPWM（空间矢量脉宽调制）
 * ============================================================ */

/**
 * @brief SVPWM 计算并输出三路 PWM 比较值
 *
 * 使用七段式 SVPWM，过调制时归一化。
 *
 * @param m    电机控制结构
 * @param vab  αβ 坐标系电压参考（单位：V）
 */
void Motor_SVPWM(MotorCtrl_t *m, AlphaBeta_t vab)
{
    /* 归一化到 [-1, 1]，除以 Vbus/2 */
    float half_vbus = m->vbus * 0.5f;
    if (half_vbus < 1e-3f) half_vbus = 1e-3f;

    float va = vab.alpha / half_vbus;
    float vb = vab.beta  / half_vbus;

    /* 计算三相参考电压（归一化，Martin法）*/
    float v1 =  vb;
    float v2 = (-vb + SQRT3 * va) * 0.5f;
    float v3 = (-vb - SQRT3 * va) * 0.5f;

    /* 确定扇区 */
    uint8_t sector = 0;
    if      (v1 >= 0 && v2 >= 0 && v3 < 0)  sector = 1;
    else if (v1 >= 0 && v2 < 0  && v3 < 0)  sector = 2;
    else if (v1 >= 0 && v2 < 0  && v3 >= 0) sector = 3;
    else if (v1 < 0  && v2 < 0  && v3 >= 0) sector = 4;
    else if (v1 < 0  && v2 >= 0 && v3 >= 0) sector = 5;
    else                                      sector = 6;

    /* 计算两个有效矢量作用时间（归一化）*/
    float t1, t2, t0;
    switch (sector) {
        case 1: t1 =  v2; t2 =  v1; break;
        case 2: t1 = -v3; t2 = -v2; break;
        case 3: t1 =  v1; t2 =  v3; break;
        case 4: t1 = -v1; t2 = -v3; break;
        case 5: t1 =  v3; t2 =  v2; break;
        case 6: t1 = -v2; t2 = -v1; break;
        default: t1 = 0; t2 = 0; break;
    }

    /* 过调制限制 */
    if ((t1 + t2) > 1.0f) {
        float k = 1.0f / (t1 + t2);
        t1 *= k;
        t2 *= k;
    }
    t0 = 1.0f - t1 - t2;

    /* 计算三相切换时刻（中心对称 SVPWM）*/
    float tcm_a, tcm_b, tcm_c;
    switch (sector) {
        case 1:
            tcm_a = t1 + t2 + t0 / 2.0f;
            tcm_b = t2 + t0 / 2.0f;
            tcm_c = t0 / 2.0f;
            break;
        case 2:
            tcm_a = t1 + t0 / 2.0f;
            tcm_b = t1 + t2 + t0 / 2.0f;
            tcm_c = t0 / 2.0f;
            break;
        case 3:
            tcm_a = t0 / 2.0f;
            tcm_b = t1 + t2 + t0 / 2.0f;
            tcm_c = t2 + t0 / 2.0f;
            break;
        case 4:
            tcm_a = t0 / 2.0f;
            tcm_b = t1 + t0 / 2.0f;
            tcm_c = t1 + t2 + t0 / 2.0f;
            break;
        case 5:
            tcm_a = t2 + t0 / 2.0f;
            tcm_b = t0 / 2.0f;
            tcm_c = t1 + t2 + t0 / 2.0f;
            break;
        case 6:
        default:
            tcm_a = t1 + t2 + t0 / 2.0f;
            tcm_b = t0 / 2.0f;
            tcm_c = t1 + t0 / 2.0f;
            break;
    }

    /* 转换为定时器比较值 */
    uint32_t cmp_a = (uint32_t)(tcm_a * MOTOR_PWM_PERIOD);
    uint32_t cmp_b = (uint32_t)(tcm_b * MOTOR_PWM_PERIOD);
    uint32_t cmp_c = (uint32_t)(tcm_c * MOTOR_PWM_PERIOD);

    /* 边界保护 */
    if (cmp_a > MOTOR_PWM_PERIOD) cmp_a = MOTOR_PWM_PERIOD;
    if (cmp_b > MOTOR_PWM_PERIOD) cmp_b = MOTOR_PWM_PERIOD;
    if (cmp_c > MOTOR_PWM_PERIOD) cmp_c = MOTOR_PWM_PERIOD;

    /* 写入定时器比较寄存器 */
    __HAL_TIM_SET_COMPARE(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_A, cmp_a);
    __HAL_TIM_SET_COMPARE(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_B, cmp_b);
    __HAL_TIM_SET_COMPARE(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_C, cmp_c);
}

/* ============================================================
 *  电机初始化
 * ============================================================ */

bool Motor_Init(MotorCtrl_t *m)
{
    m->state = MOTOR_STATE_IDLE;

    /* DRV8301 默认配置 */
    DRV8301_GetDefaultConfig(&m->drvCfg);

    if (!DRV8301_Init(&m->drvCfg)) {
        m->state = MOTOR_STATE_FAULT;
        return false;
    }

    /* 初始化 PI 控制器（参数需要根据电机参数整定）*/
    /* d轴电流环：带宽建议 500-2000 Hz */
    PID_SetParams(&m->pid_id,    0.5f, 0.01f, -1.0f, 1.0f);

    /* q轴电流环 */
    PID_SetParams(&m->pid_iq,    0.5f, 0.01f, -1.0f, 1.0f);

    /* 转速环：带宽建议 10-50 Hz，比电流环低10倍以上 */
    PID_SetParams(&m->pid_speed, 0.1f, 0.001f, -20.0f, 20.0f);

    /* 清零状态 */
    m->id_ref    = 0.0f;
    m->iq_ref    = 0.0f;
    m->speed_ref = 0.0f;
    m->theta_e   = 0.0f;
    m->vbus      = 24.0f;  /* 默认母线电压，需要 ADC 实测更新 */

    m->state = MOTOR_STATE_READY;
    return true;
}

/* ============================================================
 *  电机使能 / 停止
 * ============================================================ */

void Motor_Start(MotorCtrl_t *m)
{
    if (m->state == MOTOR_STATE_FAULT) return;

    /* 使能 DRV8301 栅极驱动 */
    DRV8301_EnableGate();

    /* 启动三路互补 PWM */
    HAL_TIM_PWM_Start(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_A);
    HAL_TIMEx_PWMN_Start(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_A);
    HAL_TIM_PWM_Start(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_B);
    HAL_TIMEx_PWMN_Start(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_B);
    HAL_TIM_PWM_Start(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_C);
    HAL_TIMEx_PWMN_Start(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_C);

    m->state = MOTOR_STATE_RUN;
}

void Motor_Stop(MotorCtrl_t *m)
{
    m->iq_ref = 0.0f;
    m->id_ref = 0.0f;
    m->state = MOTOR_STATE_STOP;
    /* 让 FOC 循环自然减到0后再停止输出 */
}

void Motor_EmergencyStop(MotorCtrl_t *m)
{
    /* 立即禁用所有 PWM 输出 */
    DRV8301_DisableGate();

    HAL_TIM_PWM_Stop(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_A);
    HAL_TIMEx_PWMN_Stop(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_A);
    HAL_TIM_PWM_Stop(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_B);
    HAL_TIMEx_PWMN_Stop(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_B);
    HAL_TIM_PWM_Stop(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_C);
    HAL_TIMEx_PWMN_Stop(&MOTOR_TIM_HANDLE, MOTOR_TIM_CH_C);

    PID_Reset(&m->pid_id);
    PID_Reset(&m->pid_iq);
    PID_Reset(&m->pid_speed);

    m->state = MOTOR_STATE_FAULT;
}

/* ============================================================
 *  设置目标
 * ============================================================ */

void Motor_SetSpeed(MotorCtrl_t *m, float speed_rpm)
{
    m->speed_ref = speed_rpm;
}

void Motor_SetTorque(MotorCtrl_t *m, float iq_ref)
{
    m->iq_ref = iq_ref;
}

/* ============================================================
 *  故障处理
 * ============================================================ */

void Motor_FaultHandler(MotorCtrl_t *m)
{
    DRV8301_ReadStatus(&m->drvStatus);

    if (m->drvStatus.fault) {
        Motor_EmergencyStop(m);

        /* TODO: 上报故障类型给上层 */
        if (m->drvStatus.oc_fault)     { /* 过流处理 */ }
        if (m->drvStatus.ot_shutdown)  { /* 过温处理 */ }
        if (m->drvStatus.pvdd_uv)      { /* 欠压处理 */ }
    }
}

/* ============================================================
 *  FOC 主循环（在定时器/ADC中断中调用，典型 20kHz）
 * ============================================================ */

/**
 * @brief FOC 主控制环
 *
 * 调用顺序：
 *  1. ADC 采样更新 ia/ib/vbus（在中断顶部完成）
 *  2. 调用本函数
 *  3. SVPWM 输出写入 TIM 比较寄存器
 *
 * 电角度 theta_e 需要由编码器或无感估算模块在外部更新。
 */
void Motor_FOC_Loop(MotorCtrl_t *m)
{
    if (m->state != MOTOR_STATE_RUN && m->state != MOTOR_STATE_STOP) return;

    /* ① 检测故障 */
    if (DRV8301_IsFault()) {
        Motor_FaultHandler(m);
        return;
    }

    /* ② Clarke 变换：三相电流 → αβ */
    m->iab = Motor_Clarke(m->ia, m->ib, m->ic);

    /* ③ Park 变换：αβ → dq */
    m->idq = Motor_Park(m->iab, m->theta_e);

    /* ④ 转速外环（如使用转速控制模式）
     *    将速度误差映射到 iq 给定
     *    注意：速度环每 N 个 FOC 周期运行一次（例如每 10 次）
     */
    /* 此处以力矩控制为主，速度外环可选接入 */
    /* m->iq_ref = PID_Calc(&m->pid_speed, m->speed_ref - m->speed_rpm); */

    /* ⑤ 电流内环（dq轴 PI）*/
    float vd = PID_Calc(&m->pid_id, m->id_ref - m->idq.d);
    float vq = PID_Calc(&m->pid_iq, m->iq_ref - m->idq.q);

    /* ⑥ 前馈解耦补偿（可选，提高动态响应）
     *    vd_ff = -ωe * Lq * iq
     *    vq_ff =  ωe * (Ld * id + ψf)
     *    需要已知电机参数（Ld/Lq/ψf/ωe），此处预留接口
     */
    m->vdq_ref.d = vd;
    m->vdq_ref.q = vq;

    /* ⑦ 逆 Park 变换：dq → αβ */
    m->vab_ref = Motor_InvPark(m->vdq_ref, m->theta_e);

    /* ⑧ SVPWM 输出 */
    Motor_SVPWM(m, m->vab_ref);

    /* ⑨ 停止状态：检测是否已降到零 */
    if (m->state == MOTOR_STATE_STOP) {
        if (m->speed_rpm > -1.0f && m->speed_rpm < 1.0f) {
            Motor_EmergencyStop(m);
            m->state = MOTOR_STATE_READY;
        }
    }
}

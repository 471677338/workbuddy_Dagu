/**
 * @file motor_control.h
 * @brief 基于 DRV8301 的三相无刷电机 SVPWM 控制层
 *        FOC（磁场定向控制）辅助模块
 *
 * 提供：
 *  - SVPWM 扇区计算与 PWM 占空比输出
 *  - Clark/Park 变换
 *  - 基础 PI 控制器
 *  - 电机运行状态机
 */

#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include "stdint.h"
#include "stdbool.h"
#include "math.h"
#include "drv8301.h"

/* ============================================================
 *  PWM 定时器（请根据实际硬件修改）
 * ============================================================ */
#include "tim.h"
#define MOTOR_TIM_HANDLE    htim1       /* 高级定时器，支持互补PWM */
#define MOTOR_PWM_PERIOD    3000        /* PWM计数周期（对应20kHz，72MHz/2/3000）*/

/* 三相 PWM 通道（互补输出：TIM_CHANNEL_1/2/3 + N通道）*/
#define MOTOR_TIM_CH_A      TIM_CHANNEL_1
#define MOTOR_TIM_CH_B      TIM_CHANNEL_2
#define MOTOR_TIM_CH_C      TIM_CHANNEL_3

/* ============================================================
 *  数学常量
 * ============================================================ */
#ifndef M_PI
#define M_PI        3.14159265358979323846f
#endif
#define SQRT3       1.73205080757f
#define SQRT3_2     0.86602540378f   /* sqrt(3)/2 */
#define ONE_OVER_SQRT3  0.57735026919f

/* ============================================================
 *  Clark / Park 变换结构体
 * ============================================================ */
typedef struct { float alpha; float beta;  } AlphaBeta_t;
typedef struct { float d;     float q;     } DQ_t;

/* ============================================================
 *  PI 控制器
 * ============================================================ */
typedef struct {
    float kp;           /* 比例系数 */
    float ki;           /* 积分系数 */
    float integrator;   /* 积分累积 */
    float out_min;      /* 输出下限 */
    float out_max;      /* 输出上限 */
} PID_t;

/* ============================================================
 *  电机状态机
 * ============================================================ */
typedef enum {
    MOTOR_STATE_IDLE    = 0,    /* 空闲，未使能 */
    MOTOR_STATE_READY   = 1,    /* 就绪，等待指令 */
    MOTOR_STATE_RUN     = 2,    /* 运行中 */
    MOTOR_STATE_FAULT   = 3,    /* 故障 */
    MOTOR_STATE_STOP    = 4     /* 减速停止中 */
} MotorState_t;

/* ============================================================
 *  电机控制主结构体
 * ============================================================ */
typedef struct {
    DRV8301_Config_t    drvCfg;         /* DRV8301 配置 */
    DRV8301_Status_t    drvStatus;      /* DRV8301 状态 */
    MotorState_t        state;          /* 电机状态 */

    float               vbus;           /* 母线电压（V）*/
    float               ia;             /* A相电流（A）*/
    float               ib;             /* B相电流（A）*/
    float               ic;             /* C相电流（A）*/

    AlphaBeta_t         iab;            /* Clark变换后 */
    DQ_t                idq;            /* Park变换后 */
    DQ_t                vdq_ref;        /* 电压参考 */
    AlphaBeta_t         vab_ref;        /* 逆Park后 */

    float               theta_e;        /* 电角度（rad）*/
    float               speed_rpm;      /* 转速（rpm）*/

    PID_t               pid_id;         /* d轴电流PI */
    PID_t               pid_iq;         /* q轴电流PI */
    PID_t               pid_speed;      /* 转速PI */

    float               id_ref;         /* d轴电流给定（弱磁控制时非零）*/
    float               iq_ref;         /* q轴电流给定（力矩控制）*/
    float               speed_ref;      /* 转速给定（rpm）*/
} MotorCtrl_t;

/* ============================================================
 *  函数声明
 * ============================================================ */

/* 初始化 */
bool Motor_Init(MotorCtrl_t *m);

/* 使能/禁用电机输出 */
void Motor_Start(MotorCtrl_t *m);
void Motor_Stop(MotorCtrl_t *m);
void Motor_EmergencyStop(MotorCtrl_t *m);

/* FOC 主循环（在 PWM 中断中调用，20kHz）*/
void Motor_FOC_Loop(MotorCtrl_t *m);

/* 故障处理 */
void Motor_FaultHandler(MotorCtrl_t *m);

/* 设置转速 */
void Motor_SetSpeed(MotorCtrl_t *m, float speed_rpm);

/* 设置力矩（直接设定 iq_ref）*/
void Motor_SetTorque(MotorCtrl_t *m, float iq_ref);

/* Clarke 变换：三相静止 → αβ */
AlphaBeta_t Motor_Clarke(float ia, float ib, float ic);

/* Park 变换：αβ → dq */
DQ_t Motor_Park(AlphaBeta_t iab, float theta);

/* 逆 Park 变换：dq → αβ */
AlphaBeta_t Motor_InvPark(DQ_t vdq, float theta);

/* SVPWM：αβ电压 → 三路占空比 */
void Motor_SVPWM(MotorCtrl_t *m, AlphaBeta_t vab);

/* PI 控制器计算 */
float PID_Calc(PID_t *pid, float error);
void  PID_Reset(PID_t *pid);

/* PI 参数设置 */
void  PID_SetParams(PID_t *pid, float kp, float ki, float out_min, float out_max);

#endif /* MOTOR_CONTROL_H */

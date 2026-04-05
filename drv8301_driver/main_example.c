/**
 * @file main_example.c
 * @brief DRV8301 + FOC 使用示例
 *
 * 典型工程集成步骤：
 *  1. 将 drv8301.h/.c 和 motor_control.h/.c 加入工程
 *  2. 根据硬件修改引脚宏定义（drv8301.h）和定时器宏定义（motor_control.h）
 *  3. 配置 SPI：CPOL=1, CPHA=1, 16bit, 最高10MHz
 *  4. 配置 TIM1 互补 PWM，开启 ADC 中断
 *  5. 在 ADC/TIM 中断中采样电流，更新 theta_e，调用 Motor_FOC_Loop()
 */

#include "drv8301.h"
#include "motor_control.h"

/* 全局电机控制实例 */
MotorCtrl_t motor;

/* ============================================================
 *  系统初始化
 * ============================================================ */
void AppInit(void)
{
    /* 电机初始化（含 DRV8301 SPI 初始化）*/
    if (!Motor_Init(&motor)) {
        /* 初始化失败：SPI 通信异常或 DRV8301 未就绪 */
        Error_Handler();
    }

    /* 设置目标转速（需要速度外环时使用）*/
    Motor_SetSpeed(&motor, 1000.0f);   /* 目标 1000 RPM */

    /* 或者直接设置力矩 */
    /* Motor_SetTorque(&motor, 2.0f);  */

    /* 启动电机 */
    Motor_Start(&motor);
}

/* ============================================================
 *  ADC 完成中断回调（典型 20kHz）
 * ============================================================ */
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc)
{
    (void)hadc;

    /* ① 读取电流 ADC 值并转换为电流（A）
     *    示例：12位ADC，参考电压3.3V，放大倍数40V/V，采样电阻0.01Ω
     *    电流 = (adc_val / 4096 * 3.3 - 1.65) / (40 * 0.01)
     */
    /* float ia_raw = (float)ADC1_CH1_VALUE / 4096.0f * 3.3f;  */
    /* motor.ia = (ia_raw - 1.65f) / (40.0f * 0.01f);          */
    /* motor.ib = ...                                           */
    /* motor.ic = -(motor.ia + motor.ib);                       */

    /* ② 更新电角度（来自编码器/Hall/无感估算）*/
    /* motor.theta_e = Encoder_GetTheta();  */

    /* ③ 更新母线电压 */
    /* motor.vbus = (float)VBUS_ADC_VALUE / 4096.0f * 3.3f * VBUS_DIVIDER; */

    /* ④ 运行 FOC 主环 */
    Motor_FOC_Loop(&motor);
}

/* ============================================================
 *  nFAULT 外部中断回调
 * ============================================================ */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == DRV8301_NFAULT_PIN) {
        /* DRV8301 故障：立即停机 */
        Motor_FaultHandler(&motor);
    }
}

/* ============================================================
 *  主循环（低频任务，1ms tick）
 * ============================================================ */
void AppLoop(void)
{
    static uint32_t last_tick = 0;
    uint32_t now = HAL_GetTick();

    if (now - last_tick >= 10) {  /* 10ms 轮询 */
        last_tick = now;

        /* 速度外环（可选：将速度环放在低频任务而非 FOC 中断）*/
        if (motor.state == MOTOR_STATE_RUN) {
            motor.iq_ref = PID_Calc(&motor.pid_speed,
                                    motor.speed_ref - motor.speed_rpm);
        }

        /* 周期性故障检测 */
        if (DRV8301_IsFault()) {
            Motor_FaultHandler(&motor);
        }
    }
}

/**
 * @file drv8301.h
 * @brief DRV8301 三相无刷电机门极驱动器 驱动头文件
 *        适用平台：STM32（HAL库）
 *
 * DRV8301 功能：
 *  - SPI 配置接口（16位帧，CPOL=1, CPHA=1，Mode3）
 *  - 6路 PWM 输入（AH/AL/BH/BL/CH/CL）
 *  - 双路电流检测放大器（CS_AMP1 / CS_AMP2）
 *  - 故障检测：nFAULT / nOCTW 引脚
 *  - 内置 Buck 稳压器（1.7V / 3.3V / 6V 可选）
 */

#ifndef DRV8301_H
#define DRV8301_H

#include "stdint.h"
#include "stdbool.h"

/* ============================================================
 *  平台适配 - 请根据实际 HAL 库修改
 * ============================================================ */
#include "main.h"       /* HAL 头文件 */
#include "spi.h"        /* SPI 句柄   */

/* ============================================================
 *  引脚定义（请根据实际硬件修改）
 * ============================================================ */
#define DRV8301_SPI_HANDLE      hspi1       /* SPI 句柄 */
#define DRV8301_CS_PORT         GPIOA
#define DRV8301_CS_PIN          GPIO_PIN_4

#define DRV8301_NFAULT_PORT     GPIOB
#define DRV8301_NFAULT_PIN      GPIO_PIN_0

#define DRV8301_NOCTW_PORT      GPIOB
#define DRV8301_NOCTW_PIN       GPIO_PIN_1

#define DRV8301_EN_GATE_PORT    GPIOC
#define DRV8301_EN_GATE_PIN     GPIO_PIN_0

/* ============================================================
 *  SPI 寄存器地址
 * ============================================================ */
#define DRV8301_REG_STATUS1     0x00U   /* 状态寄存器1（只读）*/
#define DRV8301_REG_STATUS2     0x01U   /* 状态寄存器2（只读）*/
#define DRV8301_REG_CTRL1       0x02U   /* 控制寄存器1（读写）*/
#define DRV8301_REG_CTRL2       0x03U   /* 控制寄存器2（读写）*/

/* ============================================================
 *  Status Register 1 位域
 * ============================================================ */
#define DRV8301_SR1_FAULT       (1 << 10)   /* 通用故障 */
#define DRV8301_SR1_GVDD_UV     (1 << 9)    /* 栅驱欠压 */
#define DRV8301_SR1_PVDD_UV     (1 << 8)    /* 功率级欠压 */
#define DRV8301_SR1_OTSD        (1 << 7)    /* 过温关断 */
#define DRV8301_SR1_OTW         (1 << 6)    /* 过温警告 */
#define DRV8301_SR1_FETHA_OC    (1 << 5)    /* 上桥A过流 */
#define DRV8301_SR1_FETLA_OC    (1 << 4)    /* 下桥A过流 */
#define DRV8301_SR1_FETHB_OC    (1 << 3)    /* 上桥B过流 */
#define DRV8301_SR1_FETLB_OC    (1 << 2)    /* 下桥B过流 */
#define DRV8301_SR1_FETHC_OC    (1 << 1)    /* 上桥C过流 */
#define DRV8301_SR1_FETLC_OC    (1 << 0)    /* 下桥C过流 */

/* ============================================================
 *  Control Register 1 位域
 * ============================================================ */
/* 栅极电流设置 [10:8] */
typedef enum {
    GATE_CURRENT_1_7A  = 0x00,  /* 1.7A */
    GATE_CURRENT_0_7A  = 0x01,  /* 0.7A */
    GATE_CURRENT_0_25A = 0x02   /* 0.25A */
} DRV8301_GateCurrent_t;

/* 复位方式 [7] */
#define DRV8301_CTRL1_GATE_RESET    (1 << 7)

/* OC模式 [6:5] */
typedef enum {
    OC_MODE_LATCH_SHUTDOWN = 0x00,  /* 锁存关断 */
    OC_MODE_AUTO_RETRY     = 0x01,  /* 自动重试 */
    OC_MODE_REPORT_ONLY    = 0x02,  /* 仅报告 */
    OC_MODE_DISABLED       = 0x03   /* 禁用 */
} DRV8301_OCMode_t;

/* OC调整 [4:3] */
typedef enum {
    OC_ADJ_060MV = 0x00,  /* 0.060V */
    OC_ADJ_068MV = 0x01,
    OC_ADJ_076MV = 0x02,
    OC_ADJ_086MV = 0x03,
    OC_ADJ_097MV = 0x04,
    OC_ADJ_109MV = 0x05,
    OC_ADJ_123MV = 0x06,
    OC_ADJ_138MV = 0x07,
    OC_ADJ_155MV = 0x08,
    OC_ADJ_175MV = 0x09,
    OC_ADJ_197MV = 0x0A,
    OC_ADJ_222MV = 0x0B,
    OC_ADJ_250MV = 0x0C,
    OC_ADJ_282MV = 0x0D,
    OC_ADJ_317MV = 0x0E,
    OC_ADJ_358MV = 0x0F,
    OC_ADJ_403MV = 0x10,
    OC_ADJ_454MV = 0x11,
    OC_ADJ_511MV = 0x12,
    OC_ADJ_576MV = 0x13,
    OC_ADJ_648MV = 0x14,
    OC_ADJ_730MV = 0x15,
    OC_ADJ_822MV = 0x16,
    OC_ADJ_926MV = 0x17,
    OC_ADJ_1043MV= 0x18,
    OC_ADJ_1175MV= 0x19,
    OC_ADJ_1324MV= 0x1A,
    OC_ADJ_1491MV= 0x1B,
    OC_ADJ_1679MV= 0x1C,
    OC_ADJ_1892MV= 0x1D,
    OC_ADJ_2131MV= 0x1E,
    OC_ADJ_2400MV= 0x1F
} DRV8301_OCAdj_t;

/* PWM 模式 [1] */
typedef enum {
    PWM_MODE_6_INPUT  = 0x00,   /* 6路独立PWM输入 */
    PWM_MODE_3_INPUT  = 0x01    /* 3路PWM输入（内部死区） */
} DRV8301_PWMMode_t;

/* ============================================================
 *  Control Register 2 位域
 * ============================================================ */
/* 电流放大器增益 [3:2] */
typedef enum {
    CS_GAIN_10  = 0x00,     /* 10 V/V */
    CS_GAIN_20  = 0x01,     /* 20 V/V */
    CS_GAIN_40  = 0x02,     /* 40 V/V */
    CS_GAIN_80  = 0x03      /* 80 V/V */
} DRV8301_CSGain_t;

/* 直流校准 [1] - 短路放大器输入到GND用于校准 */
#define DRV8301_CTRL2_DC_CAL    (1 << 1)

/* OC_TOFF [0] */
#define DRV8301_CTRL2_OC_TOFF   (1 << 0)

/* ============================================================
 *  驱动配置结构体
 * ============================================================ */
typedef struct {
    DRV8301_GateCurrent_t gateCurrent;  /* 栅极驱动电流 */
    DRV8301_OCMode_t      ocMode;       /* 过流保护模式 */
    DRV8301_OCAdj_t       ocAdj;        /* 过流阈值调整 */
    DRV8301_PWMMode_t     pwmMode;      /* PWM输入模式 */
    DRV8301_CSGain_t      csGain;       /* 电流采样增益 */
} DRV8301_Config_t;

/* ============================================================
 *  状态结构体
 * ============================================================ */
typedef struct {
    uint16_t status1;           /* 状态寄存器1原始值 */
    uint16_t status2;           /* 状态寄存器2原始值 */
    bool     fault;             /* 是否有故障 */
    bool     oc_fault;          /* 过流故障 */
    bool     ot_shutdown;       /* 过温关断 */
    bool     ot_warning;        /* 过温警告 */
    bool     pvdd_uv;           /* 功率级欠压 */
    bool     gvdd_uv;           /* 栅驱欠压 */
} DRV8301_Status_t;

/* ============================================================
 *  函数声明
 * ============================================================ */

/**
 * @brief  初始化 DRV8301
 * @param  cfg  配置参数
 * @retval true  初始化成功
 *         false 通信失败
 */
bool DRV8301_Init(const DRV8301_Config_t *cfg);

/**
 * @brief  使能栅极驱动（拉高 EN_GATE）
 */
void DRV8301_EnableGate(void);

/**
 * @brief  禁用栅极驱动（拉低 EN_GATE，紧急停机）
 */
void DRV8301_DisableGate(void);

/**
 * @brief  读取状态寄存器并解析故障信息
 * @param  status  输出状态结构体指针
 */
void DRV8301_ReadStatus(DRV8301_Status_t *status);

/**
 * @brief  清除故障（通过读取状态寄存器触发清除）
 */
void DRV8301_ClearFaults(void);

/**
 * @brief  检查 nFAULT 引脚电平
 * @retval true  有故障
 */
bool DRV8301_IsFault(void);

/**
 * @brief  写控制寄存器
 * @param  reg   寄存器地址（0x02 或 0x03）
 * @param  data  11位数据
 * @retval SPI 返回值（可忽略）
 */
uint16_t DRV8301_WriteReg(uint8_t reg, uint16_t data);

/**
 * @brief  读寄存器
 * @param  reg   寄存器地址
 * @retval 11位数据
 */
uint16_t DRV8301_ReadReg(uint8_t reg);

/**
 * @brief  获取默认配置（推荐用于快速初始化）
 * @param  cfg  输出默认配置
 */
void DRV8301_GetDefaultConfig(DRV8301_Config_t *cfg);

#endif /* DRV8301_H */

/**
 * @file drv8301.c
 * @brief DRV8301 三相无刷电机门极驱动器 驱动实现
 *        适用平台：STM32（HAL库）
 *
 * SPI 时序要求：
 *   - CPOL=1, CPHA=1（Mode 3）
 *   - 最高时钟频率：10 MHz
 *   - 帧格式：16位 MSB First
 *   - CS低有效，每次传输结束拉高
 *
 *  16位帧格式：
 *   [15]    : R/W = 0写 / 1读
 *   [14:11] : 寄存器地址（4位）
 *   [10:0]  : 数据（11位）
 */

#include "drv8301.h"

/* ============================================================
 *  内部宏定义
 * ============================================================ */
#define DRV8301_RW_BIT_WRITE    (0 << 15)
#define DRV8301_RW_BIT_READ     (1 << 15)
#define DRV8301_ADDR_SHIFT      11
#define DRV8301_DATA_MASK       0x07FFU  /* 低11位数据 */

#define CS_LOW()   HAL_GPIO_WritePin(DRV8301_CS_PORT, DRV8301_CS_PIN, GPIO_PIN_RESET)
#define CS_HIGH()  HAL_GPIO_WritePin(DRV8301_CS_PORT, DRV8301_CS_PIN, GPIO_PIN_SET)

/* ============================================================
 *  SPI 底层收发
 * ============================================================ */

/**
 * @brief  SPI 发送并接收 16 位数据
 * @param  txData  发送的16位帧
 * @retval 接收的16位帧
 */
static uint16_t DRV8301_SPI_Transfer(uint16_t txData)
{
    uint8_t txBuf[2];
    uint8_t rxBuf[2] = {0, 0};

    txBuf[0] = (uint8_t)(txData >> 8);    /* 高字节先发（MSB First）*/
    txBuf[1] = (uint8_t)(txData & 0xFF);

    CS_LOW();
    /* 等待 tCSS（最小250ns），此处用空循环模拟，正式项目用精确延时 */
    for (volatile int i = 0; i < 5; i++) {}

    HAL_SPI_TransmitReceive(&DRV8301_SPI_HANDLE, txBuf, rxBuf, 2, 10);

    /* 等待 tCSH（最小250ns）*/
    for (volatile int i = 0; i < 5; i++) {}
    CS_HIGH();

    return ((uint16_t)rxBuf[0] << 8) | rxBuf[1];
}

/* ============================================================
 *  寄存器读写
 * ============================================================ */

/**
 * @brief  写寄存器
 *  帧格式: [15]=0(写), [14:11]=地址, [10:0]=数据
 */
uint16_t DRV8301_WriteReg(uint8_t reg, uint16_t data)
{
    uint16_t frame = DRV8301_RW_BIT_WRITE
                   | ((uint16_t)(reg & 0x0F) << DRV8301_ADDR_SHIFT)
                   | (data & DRV8301_DATA_MASK);
    return DRV8301_SPI_Transfer(frame);
}

/**
 * @brief  读寄存器
 *  先发送读命令，再发一次空帧取回数据
 *  DRV8301 读时序：第一帧发读命令，第二帧返回值
 */
uint16_t DRV8301_ReadReg(uint8_t reg)
{
    uint16_t frame = DRV8301_RW_BIT_READ
                   | ((uint16_t)(reg & 0x0F) << DRV8301_ADDR_SHIFT);

    DRV8301_SPI_Transfer(frame);        /* 第一帧：发读命令 */
    uint16_t result = DRV8301_SPI_Transfer(0x0000);  /* 第二帧：读回数据 */

    return result & DRV8301_DATA_MASK;
}

/* ============================================================
 *  GPIO 操作
 * ============================================================ */

void DRV8301_EnableGate(void)
{
    HAL_GPIO_WritePin(DRV8301_EN_GATE_PORT, DRV8301_EN_GATE_PIN, GPIO_PIN_SET);
    HAL_Delay(1);  /* 等待内部稳定（推荐 ≥ 1ms）*/
}

void DRV8301_DisableGate(void)
{
    HAL_GPIO_WritePin(DRV8301_EN_GATE_PORT, DRV8301_EN_GATE_PIN, GPIO_PIN_RESET);
}

bool DRV8301_IsFault(void)
{
    /* nFAULT 低电平有效 */
    return (HAL_GPIO_ReadPin(DRV8301_NFAULT_PORT, DRV8301_NFAULT_PIN) == GPIO_PIN_RESET);
}

/* ============================================================
 *  状态读取
 * ============================================================ */

void DRV8301_ReadStatus(DRV8301_Status_t *status)
{
    if (status == NULL) return;

    status->status1 = DRV8301_ReadReg(DRV8301_REG_STATUS1);
    status->status2 = DRV8301_ReadReg(DRV8301_REG_STATUS2);

    uint16_t s1 = status->status1;

    status->fault       = (s1 & DRV8301_SR1_FAULT)    != 0;
    status->gvdd_uv     = (s1 & DRV8301_SR1_GVDD_UV)  != 0;
    status->pvdd_uv     = (s1 & DRV8301_SR1_PVDD_UV)  != 0;
    status->ot_shutdown = (s1 & DRV8301_SR1_OTSD)      != 0;
    status->ot_warning  = (s1 & DRV8301_SR1_OTW)       != 0;

    /* 任意桥臂过流 */
    status->oc_fault = (s1 & (DRV8301_SR1_FETHA_OC | DRV8301_SR1_FETLA_OC |
                               DRV8301_SR1_FETHB_OC | DRV8301_SR1_FETLB_OC |
                               DRV8301_SR1_FETHC_OC | DRV8301_SR1_FETLC_OC)) != 0;
}

void DRV8301_ClearFaults(void)
{
    /* 读取状态寄存器1即可清除锁存故障 */
    DRV8301_ReadReg(DRV8301_REG_STATUS1);
    DRV8301_ReadReg(DRV8301_REG_STATUS2);
}

/* ============================================================
 *  默认配置
 * ============================================================ */

void DRV8301_GetDefaultConfig(DRV8301_Config_t *cfg)
{
    if (cfg == NULL) return;
    cfg->gateCurrent = GATE_CURRENT_1_7A;
    cfg->ocMode      = OC_MODE_LATCH_SHUTDOWN;
    cfg->ocAdj       = OC_ADJ_250MV;       /* 0.25V 过流阈值（低侧电阻0.01Ω → 25A）*/
    cfg->pwmMode     = PWM_MODE_6_INPUT;
    cfg->csGain      = CS_GAIN_40;          /* 40 V/V，适合低侧电流采样 */
}

/* ============================================================
 *  初始化
 * ============================================================ */

bool DRV8301_Init(const DRV8301_Config_t *cfg)
{
    /* ① 拉低 EN_GATE 复位芯片 */
    DRV8301_DisableGate();
    HAL_Delay(10);  /* 等待内部POR完成（最少1ms，推荐10ms）*/

    /* ② 拉高 EN_GATE 使能 */
    DRV8301_EnableGate();

    /* ③ 写控制寄存器1
     *   [10:8] gateCurrent
     *   [7]    0 - 正常模式（1=强制PVDD_OCP）
     *   [6:5]  ocMode
     *   [4:0]  ocAdj
     *   [2]    0 - 6路PWM 或 [1]=1 3路PWM
     *   [1]    PWM mode
     */
    uint16_t ctrl1 = 0;
    ctrl1 |= ((uint16_t)(cfg->gateCurrent & 0x03) << 8);
    ctrl1 |= ((uint16_t)(cfg->ocMode      & 0x03) << 5);
    ctrl1 |= ((uint16_t)(cfg->ocAdj       & 0x1F) << 0);
    if (cfg->pwmMode == PWM_MODE_3_INPUT) {
        ctrl1 |= (1 << 2);  /* 3路PWM模式 */
    }

    DRV8301_WriteReg(DRV8301_REG_CTRL1, ctrl1);
    HAL_Delay(1);

    /* ④ 写控制寄存器2
     *   [3:2]  csGain
     */
    uint16_t ctrl2 = 0;
    ctrl2 |= ((uint16_t)(cfg->csGain & 0x03) << 2);

    DRV8301_WriteReg(DRV8301_REG_CTRL2, ctrl2);
    HAL_Delay(1);

    /* ⑤ 回读验证 */
    uint16_t readback1 = DRV8301_ReadReg(DRV8301_REG_CTRL1);
    uint16_t readback2 = DRV8301_ReadReg(DRV8301_REG_CTRL2);

    if (readback1 != ctrl1 || readback2 != ctrl2) {
        /* SPI 通信失败或寄存器未正确写入 */
        return false;
    }

    /* ⑥ 清除上电产生的故障 */
    DRV8301_ClearFaults();

    return true;
}

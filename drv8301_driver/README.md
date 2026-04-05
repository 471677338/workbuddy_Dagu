# DRV8301 电机驱动代码说明

## 文件结构

```
drv8301_driver/
├── drv8301.h           # DRV8301 芯片驱动头文件
├── drv8301.c           # DRV8301 芯片驱动实现（SPI通信、寄存器配置）
├── motor_control.h     # FOC 电机控制层头文件
├── motor_control.c     # FOC 控制实现（Clarke/Park变换、SVPWM、PI控制器）
└── main_example.c      # 使用示例（中断回调、主循环）
```

---

## 硬件连接

| DRV8301 引脚 | MCU 说明 |
|-------------|---------|
| SCLK / SDI / SDO / nSCS | SPI1（Mode3，16bit，≤10MHz）|
| EN_GATE | GPIO 输出（推挽）|
| nFAULT | GPIO 输入 + 外部中断（下降沿）|
| nOCTW  | GPIO 输入（可选轮询）|
| AH/AL/BH/BL/CH/CL | TIM1 互补 PWM 输出（6路）|
| SO1/SO2 | ADC 输入（电流采样放大器输出）|
| PVDD | 功率级电源（8-60V）|
| GVDD | 栅驱电源（内部 Buck 或外部 15V）|

---

## SPI 配置

```
模式：CPOL=1, CPHA=1（Mode 3）
字长：16 bit
位序：MSB First
时钟：≤ 10 MHz
CS ：软件控制（每次传输完成后拉高）
```

### 帧格式（16位）

```
[15]     : R/W = 0(写) / 1(读)
[14:11]  : 寄存器地址（4位）
[10:0]   : 数据（11位）
```

---

## 快速集成步骤

### 1. 修改引脚定义（drv8301.h）

```c
#define DRV8301_SPI_HANDLE      hspi1       // 修改为实际SPI句柄
#define DRV8301_CS_PORT         GPIOA       // 片选引脚
#define DRV8301_CS_PIN          GPIO_PIN_4
#define DRV8301_EN_GATE_PORT    GPIOC
#define DRV8301_EN_GATE_PIN     GPIO_PIN_0
```

### 2. 修改 PWM 定时器（motor_control.h）

```c
#define MOTOR_TIM_HANDLE    htim1
#define MOTOR_PWM_PERIOD    3000     // 72MHz / 2 / 3000 = 12kHz
                                     // 72MHz / 2 / 1800 = 20kHz
```

### 3. 初始化

```c
MotorCtrl_t motor;

// 在 main() 中
Motor_Init(&motor);
Motor_SetSpeed(&motor, 1000.0f);  // 1000 RPM
Motor_Start(&motor);
```

### 4. 在中断中运行 FOC

```c
// ADC/TIM 更新中断（20kHz）
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc) {
    motor.ia = read_current_A();   // 采样A相电流
    motor.ib = read_current_B();   // 采样B相电流
    motor.ic = -(motor.ia + motor.ib);
    motor.theta_e = encoder_get_theta();  // 获取电角度
    motor.vbus    = read_vbus();          // 母线电压
    Motor_FOC_Loop(&motor);
}
```

### 5. 故障处理

```c
// nFAULT 外部中断
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
    if (GPIO_Pin == DRV8301_NFAULT_PIN) {
        Motor_FaultHandler(&motor);
    }
}
```

---

## 关键参数整定

### 电流环 PI（需要根据电机参数计算）

| 参数 | 建议值 | 说明 |
|------|--------|------|
| kp   | Rs / (2*π*BW*Ls) | BW = 500~2000 Hz |
| ki   | kp * (Rs/Ls) / fs | fs = 采样频率 |

### 过流阈值（OC_ADJ）

```
阈值电流 = OC_ADJ_voltage / 采样电阻值
例：OC_ADJ_250MV = 0.25V，采样电阻 0.01Ω → 25A 过流保护
```

### 电流放大器增益（CS_GAIN）

```
增益选择：确保满量程电流对应的输出电压 ≤ VREF（通常 3.3V）
公式：Gain ≤ (VREF/2) / (I_max * R_shunt)
例：I_max=20A, R_shunt=0.01Ω → Gain ≤ 1.65/(20*0.01) = 8.25 → 选 CS_GAIN_10
```

---

## 注意事项

1. **上电时序**：EN_GATE 需要在 SPI 初始化后再拉高，否则 DRV8301 的 SPI 不可用
2. **SPI 读时序**：DRV8301 需要两次 SPI 传输才能读回数据（第一帧发命令，第二帧读数据）
3. **死区时间**：6路PWM模式下死区由 TIM1 硬件控制，需要在 CubeMX 中配置适当死区（通常 200-500ns）
4. **电流采样时刻**：在 PWM 中心（计数器溢出/下溢时）触发 ADC 采样，避免开关噪声
5. **PVDD 范围**：DRV8301 支持 8-60V，超出此范围会触发欠压保护

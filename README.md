# TouchSky-SmartString（无手势版）

利用手机传感器（加速度计、陀螺仪、磁力计）进行姿态解算，通过连续体感映射控制 Tello 无人机飞行。

## 当前能力
1. 传感器采集与卡尔曼滤波平滑。
2. 手机姿态映射为 RC 指令（`lr/fb`）。
3. 离合（Deadman Switch）：按住控制，松手立即悬停。
4. 指令节流与心跳检查，降低网络拥塞风险。

## 目录结构
- `main.py`：程序入口
- `src/app/ui_main.py`：UI 与主控循环
- `src/sensor_fusion/`：传感器采集与融合
- `src/gesture_mapping/attitude_mapper.py`：姿态映射
- `src/communication/tello_controller.py`：Tello 控制接口
- `config/control_profile.json`：控制参数配置
- `tests/`：单元测试

## 参数配置
`config/control_profile.json` 支持以下参数：
- `loop_interval`：主循环周期（秒）
- `send_interval`：网络发送最小间隔（秒）
- `max_tilt_angle`：达到满速的倾斜角（度）
- `dead_zone`：姿态死区角度（度）
- `response_expo`：响应曲线指数（越大中心越细腻）
- `command_smoothing`：指令平滑系数（0-1）
- `max_delta_per_tick`：每帧最大指令变化量（1-100）

## 本地运行
```bash
pip install -r requirements.txt
python main.py
```

## 测试
```bash
python -m unittest discover -s tests -v
```

开发环境：Python 3.9（Conda `py3.9`）。

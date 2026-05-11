# TouchSky-SmartString 开发进度与执行日志（无手势版）

## 一、当前架构（单模式）
控制链路已收敛为：

`手机端传感器 (Plyer)` => `数据采集` => `卡尔曼滤波` => `姿态解算 (Roll/Pitch)` => `离合保护 + 指令节流` => `Tello 执行 (djitellopy)`

核心设计目标：
1. 连续体感控制：手机倾斜映射为无人机速度（`lr/fb`）。
2. 死人开关（离合）：按住控制、松手即悬停。
3. 安全优先：指令节流、心跳保活、异常时归零。

## 二、当前代码状态
1. 传感器融合：`src/sensor_fusion/kalman_filter.py` 可用。
2. 姿态映射：`src/gesture_mapping/attitude_mapper.py` 可用（当前仅保留该能力）。
3. UI 主控：`src/app/ui_main.py` 已去除手势仲裁，保留连续姿态控制闭环。
4. 通信控制：`src/communication/tello_controller.py` 可用。

## 三、执行计划（Step-by-Step）
1. [x] Step 1：把无手势版计划写入日志（本节）。
2. [x] Step 2：移除手势相关遗留文件与引用（`dtw_matcher.py`、`record_gesture.py`、`config/gestures.json`）。
3. [x] Step 3：收敛通信实现（删除 BLE 占位实现，明确 Wi-Fi/Tello 为唯一链路）。
4. [x] Step 4：增加控制参数配置（dead zone / max tilt / loop interval）。
5. [x] Step 5：补充姿态映射单元测试（死区、饱和、离合关闭）。
6. [x] Step 6：同步 README 与执行记录，形成可交付说明。

## 四、执行记录
### [2026-04-17] Step 1 完成
- 已完成：将“无手势版”目标、计划与步骤写入 `dev_log.md`。

### [2026-04-17] Step 2 完成
- 已删除：`src/gesture_mapping/dtw_matcher.py`
- 已删除：`src/tools/record_gesture.py`
- 已删除：`config/gestures.json`

### [2026-04-17] Step 3 完成
- 已删除：`src/communication/ble_sender.py`
- 通信实现统一为：`djitellopy + Tello Wi-Fi`。

### [2026-04-17] Step 4 完成
- 已新增：`config/control_profile.json`。
- 已改造：`src/app/ui_main.py` 支持读取 `loop_interval`、`send_interval`、`max_tilt_angle`、`dead_zone`。

### [2026-04-17] Step 5 完成
- 已新增测试：`tests/test_attitude_mapper.py`。
- 已覆盖：离合关闭归零、死区抑制、极限姿态饱和。

### [2026-04-17] Step 6 完成
- 已更新：`README.md`（无手势版能力、配置说明、运行与测试指引）。
- 当前状态：可按“连续姿态控制 + 离合保护”路径持续迭代。

import numpy as np

class AttitudeMapper:
    """
    连续姿态映射模块：
    将手机的倾斜角度（欧拉角：俯仰与横滚）映射为无人机在水平面的平移速度。
    适合实现类似于“虚拟摇杆”的丝滑体感控制。
    """
    def __init__(
        self,
        max_tilt_angle=45.0,
        dead_zone=5.0,
        response_expo=1.35,
        command_smoothing=0.35,
        max_delta_per_tick=20,
    ):
        """
        :param max_tilt_angle: 手机倾斜多少度时无人机达到全速(100)
        :param dead_zone: 死区角度，防止手轻微抖动导致漂移（单位：度）
        :param response_expo: 响应曲线指数（>1 时中心更细腻，边缘仍可打满）
        :param command_smoothing: 指令平滑系数（0-1，越大越跟手）
        :param max_delta_per_tick: 每个主循环允许的最大指令变化量，抑制抖动和突变
        """
        self.max_tilt_angle = max_tilt_angle
        self.dead_zone = dead_zone
        self.response_expo = response_expo
        self.command_smoothing = command_smoothing
        self.max_delta_per_tick = max_delta_per_tick
        self.prev_cmds = {"lr": 0, "fb": 0, "ud": 0, "yaw": 0}

    def _apply_dead_zone_and_scale(self, angle):
        """
        应用死区并按比例将其映射至 -100 到 100 之间
        """
        if abs(angle) < self.dead_zone:
            return 0.0
            
        # 根据倾斜的方向，减去死区的偏移量，避免启动瞬间速度跳变
        effective_angle = angle - np.sign(angle) * self.dead_zone
        effective_max = self.max_tilt_angle - self.dead_zone
        
        # 截断与归一化
        ratio = np.clip(effective_angle / effective_max, -1.0, 1.0)
        shaped = np.sign(ratio) * (abs(ratio) ** self.response_expo)
        return int(shaped * 100)

    def _smooth_axis(self, key, target):
        prev = self.prev_cmds[key]
        delta = target - prev
        limited_delta = int(np.clip(delta, -self.max_delta_per_tick, self.max_delta_per_tick))
        stepped = prev + limited_delta
        blended = (1.0 - self.command_smoothing) * prev + self.command_smoothing * stepped
        return int(np.clip(round(blended), -100, 100))

    def map_to_commands(self, gravity_vals, clutch_pressed=True):
        """
        根据重力加速度矢量解算手机姿态并输出RC指令。
        :param gravity_vals: [gx, gy, gz] 滤波后的重力/加速度数据
        :param clutch_pressed: 屏幕上的“离合”由于是否被按下，False时直接输出0悬停。
        :return: commands字典
        """
        cmds = {"lr": 0, "fb": 0, "ud": 0, "yaw": 0}
        
        if not clutch_pressed:
            self.prev_cmds = cmds.copy()
            return cmds

        gx, gy, gz = gravity_vals

        # 安全防御，避免自由落体时出现除0异常
        norm = np.linalg.norm(gravity_vals)
        if norm < 0.1: 
            return cmds

        # 换算为俯仰角 (Pitch) 和横滚角 (Roll)
        # 假设参考系：平放桌面 z=9.8, 屏幕右倾翻转影响 x，机头前倾起降影响 y
        pitch_rad = np.arctan2(gy, np.sqrt(gx**2 + gz**2))
        roll_rad = np.arctan2(-gx, gz)

        pitch_deg = np.degrees(pitch_rad)
        roll_deg = np.degrees(roll_rad)

        # 映射
        # 手机前倾(pitch < 0) -> 无人机前进, 这个符号取决于你的手机具体传感器主轴方向，后续可在调试中反转。
        cmds["fb"] = self._apply_dead_zone_and_scale(-pitch_deg)
        # 手机右倾(roll > 0) -> 无人机右移
        cmds["lr"] = self._apply_dead_zone_and_scale(roll_deg)

        smoothed = {
            "lr": self._smooth_axis("lr", cmds["lr"]),
            "fb": self._smooth_axis("fb", cmds["fb"]),
            "ud": self._smooth_axis("ud", cmds["ud"]),
            "yaw": self._smooth_axis("yaw", cmds["yaw"]),
        }
        self.prev_cmds = smoothed.copy()
        return smoothed


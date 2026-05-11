import sys
import os
import time
import json

# 将项目根目录加入到环境变量中，方便绝对引入
curr_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(curr_dir, '../../'))
if project_root not in sys.path:
    sys.path.append(project_root)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from src.sensor_fusion.data_collector import SensorDataCollector
from src.sensor_fusion.kalman_filter import SensorFusion
from src.gesture_mapping.attitude_mapper import AttitudeMapper
from src.communication.tello_controller import DroneController

class TouchSkyUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.clutch_pressed = False
        self.is_connected = False

        profile = self._load_control_profile()
        self.loop_interval = profile["loop_interval"]
        self.send_interval = profile["send_interval"]
        
        # 初始化核心模块
        self.collector = SensorDataCollector()
        self.collector.start_sensors()
        self.kf = SensorFusion(dt=self.loop_interval)
        self.attitude_mapper = AttitudeMapper(
            max_tilt_angle=profile["max_tilt_angle"],
            dead_zone=profile["dead_zone"],
            response_expo=profile["response_expo"],
            command_smoothing=profile["command_smoothing"],
            max_delta_per_tick=int(profile["max_delta_per_tick"]),
        )
        self.drone = DroneController()
        
        # 记录上一次发送的指令与时间（用于降帧减负）
        self.last_sent_cmd = None
        self.last_sent_time = 0
        
        self.build_ui()
        Clock.schedule_interval(self.main_loop, self.loop_interval)

    def _load_control_profile(self):
        config_path = os.path.join(project_root, "config", "control_profile.json")
        defaults = {
            "loop_interval": 0.04,
            "send_interval": 0.06,
            "max_tilt_angle": 45.0,
            "dead_zone": 5.0,
            "response_expo": 1.35,
            "command_smoothing": 0.35,
            "max_delta_per_tick": 20.0,
        }
        if not os.path.exists(config_path):
            return defaults
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return defaults

        profile = defaults.copy()
        for key in defaults:
            val = data.get(key)
            if isinstance(val, (int, float)):
                profile[key] = float(val)

        if profile["loop_interval"] <= 0:
            profile["loop_interval"] = defaults["loop_interval"]
        if profile["send_interval"] <= 0:
            profile["send_interval"] = defaults["send_interval"]
        if profile["max_tilt_angle"] <= 0:
            profile["max_tilt_angle"] = defaults["max_tilt_angle"]
        if profile["dead_zone"] < 0 or profile["dead_zone"] >= profile["max_tilt_angle"]:
            profile["dead_zone"] = defaults["dead_zone"]
        if profile["response_expo"] < 1.0:
            profile["response_expo"] = defaults["response_expo"]
        if profile["command_smoothing"] <= 0 or profile["command_smoothing"] > 1.0:
            profile["command_smoothing"] = defaults["command_smoothing"]
        if profile["max_delta_per_tick"] <= 0 or profile["max_delta_per_tick"] > 100:
            profile["max_delta_per_tick"] = defaults["max_delta_per_tick"]
        return profile
        
    def build_ui(self):
        # 状态面板
        self.status_label = Label(text="状态: 待命 | 离合: 松开", size_hint=(1, 0.2))
        self.add_widget(self.status_label)
        
        self.cmd_label = Label(text="控制指令: [lr: 0, fb: 0, ud: 0, yaw: 0]", size_hint=(1, 0.2))
        self.add_widget(self.cmd_label)
        
        # 连接按钮
        self.btn_connect = Button(text="连接 Tello 并起飞", size_hint=(1, 0.2))
        self.btn_connect.bind(on_press=self.toggle_drone)
        self.add_widget(self.btn_connect)
        
        # 大面积的离合按钮 (死机拉杆)
        self.btn_clutch = Button(text="[死人开关 / 离合]\n按住此处倾斜手机控制，松开即刻悬停", size_hint=(1, 0.4), background_color=[1, 0.3, 0.3, 1])
        # 绑定按下和抬起事件
        self.btn_clutch.bind(on_press=self.clutch_down)
        self.btn_clutch.bind(on_release=self.clutch_up)
        self.add_widget(self.btn_clutch)

    def toggle_drone(self, instance):
        if not self.is_connected:
            self.status_label.text = "状态: 正在连接..."
            if self.drone.connect():
                self.is_connected = True
                self.btn_connect.text = "降落并断开"
                self.drone.takeoff()
                self.status_label.text = "状态: 飞行中 (未解锁离合) | 离合: 松开"
            else:
                self.status_label.text = "状态: 连接失败，请检查 Wi-Fi"
        else:
            self.drone.land()
            self.is_connected = False
            self.btn_connect.text = "连接 Tello 并起飞"
            self.status_label.text = "状态: 已降落待命 | 离合: 松开"
            
    def clutch_down(self, instance):
        self.clutch_pressed = True
        self.btn_clutch.background_color = [0.3, 1, 0.3, 1] # 变绿
        if self.is_connected:
            self.status_label.text = "状态: 体感激活中！ | 离合: 压下"
        
    def clutch_up(self, instance):
        self.clutch_pressed = False
        self.btn_clutch.background_color = [1, 0.3, 0.3, 1] # 变红
        # 松开离合，立即紧急制动/悬停
        if self.is_connected:
            self.status_label.text = "状态: 自动悬停守卫中 | 离合: 松开"
            self.drone.halt()
            self.cmd_label.text = "控制指令: 紧急悬停 [0, 0, 0, 0]"

    def main_loop(self, dt):
        """传感器获取、滤波处理、决策融合的主循环"""
        raw_data = self.collector.collect_sensor_data()
        
        # extract accelerometer info 
        if not raw_data or 'accelerometer' not in raw_data:
            return
            
        accel = raw_data['accelerometer']
        if not accel or len(accel) != 3:
            return
            
        # 1. 滤波与平滑
        smoothed_g, _ = self.kf.process_data(accel)
        current_time = time.time()

        cmds = self.attitude_mapper.map_to_commands(smoothed_g, self.clutch_pressed)
        
        if self.clutch_pressed:
            self.cmd_label.text = f"控制指令 (姿态): lr:{cmds['lr']}, fb:{cmds['fb']}"
            
            # 只有指令变化或发送间隔达到阈值时才真正下发，减轻网络负载
            if (cmds != self.last_sent_cmd) or (current_time - self.last_sent_time > self.send_interval):
                if self.is_connected:
                    self.drone.send_rc_control(cmds['lr'], cmds['fb'], cmds['ud'], cmds['yaw'])
                self.last_sent_cmd = cmds.copy()
                self.last_sent_time = current_time
        
        # 给心跳检查一下，防断联
        if self.is_connected:
            self.drone.check_heartbeat()

class TouchSkyApp(App):
    def build(self):
        return TouchSkyUI()

if __name__ == '__main__':
    TouchSkyApp().run()

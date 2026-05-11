# tello_controller.py
# 描述: 封装对 Tello 无人机的控制指令接口，实现与底层硬件的安全通信
import time
import logging

try:
    from djitellopy import Tello
    TELLO_IMPORT_ERROR = None
except ImportError as exc:
    Tello = None
    TELLO_IMPORT_ERROR = str(exc)

class DroneController:
    def __init__(self):
        self.tello = Tello() if Tello is not None else None
        self.is_available = self.tello is not None
        self.is_connected = False
        self.is_flying = False
        self.last_command_time = time.time()
        
        # 配置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("DroneController")

    def connect(self):
        """
        连接无人机并获取电量
        注意: 需要先将设备的 Wi-Fi 连接到 Tello 的热点
        """
        if not self.is_available:
            self.logger.error(f"djitellopy 不可用，无法连接 Tello: {TELLO_IMPORT_ERROR}")
            return False

        try:
            self.tello.connect()
            self.is_connected = True
            battery = self.tello.get_battery()
            self.logger.info(f"Tello 已连接. 当前电量: {battery}%")
            return True
        except Exception as e:
            self.logger.error(f"连接 Tello 失败: {e}")
            self.is_connected = False
            return False

    def takeoff(self):
        if not self.is_available or not self.is_connected:
            self.logger.warning("未连接，无法起飞")
            return
        self.logger.info("起飞中...")
        self.tello.takeoff()
        self.is_flying = True

    def land(self):
        if not self.is_available or not self.is_connected:
            return
        self.logger.info("降落中...")
        self.tello.land()
        self.is_flying = False

    def send_rc_control(self, left_right_velocity, forward_backward_velocity, up_down_velocity, yaw_velocity):
        """
        发送 RC 控制指令（全向速度控制）
        参数范围 -100 到 100
        """
        if not self.is_available or not self.is_connected:
            return
        self.tello.send_rc_control(left_right_velocity, forward_backward_velocity, up_down_velocity, yaw_velocity)
        self.last_command_time = time.time()

    def halt(self):
        """
        紧急悬停
        """
        self.logger.info("紧急悬停！")
        self.send_rc_control(0, 0, 0, 0)
        
    def check_heartbeat(self):
        """
        心跳检查：如果超过一定时间没有下达指令，自动悬停以防撞壁
        建议放入独立线程或主循环调用
        """
        if self.is_flying and (time.time() - self.last_command_time) > 2.0:
            self.logger.warning("超时未收到指令，自动悬停。")
            self.halt()


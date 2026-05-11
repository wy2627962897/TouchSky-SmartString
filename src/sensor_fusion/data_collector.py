import time
import random

try:
    from plyer import accelerometer, gyroscope, compass
    PLYER_AVAILABLE = True
except ImportError:
    accelerometer = None
    gyroscope = None
    compass = None
    PLYER_AVAILABLE = False
    print("警告: 未安装或无法导入 plyer，已切换为【模拟数据模式】。")

class SensorDataCollector:
    def __init__(self):
        self.is_running = False
        self.mock_mode = False

    def start_sensors(self):
        """开启手机硬件传感器"""
        if not PLYER_AVAILABLE:
            self.is_running = True
            self.mock_mode = True
            return

        try:
            accelerometer.enable()
            gyroscope.enable()
            compass.enable()
            self.is_running = True
            self.mock_mode = False
            print("传感器已启动")
        except (AttributeError, NotImplementedError):
            print("警告: 当前平台不支持调用硬件传感器（通常是因为在电脑主机上运行），已自动切换为【模拟数据模式】用于开发测试。")
            self.is_running = True
            self.mock_mode = True
        except Exception as e:
            print(f"启动传感器失败: {e}")

    def stop_sensors(self):
        """关闭传感器以节省电量"""
        if not PLYER_AVAILABLE:
            self.is_running = False
            return

        try:
            accelerometer.disable()
            gyroscope.disable()
            compass.disable()
            self.is_running = False
            print("传感器已关闭")
        except Exception:
            pass

    def collect_sensor_data(self):
        """
        获取当前时间戳下的加速度计、陀螺仪、磁力计数据
        

        """
        if not self.is_running:
            return None
        
        if self.mock_mode:
            # 模拟模式下生成假数据，方便PC端直接进行算法测试
            return {
                "timestamp": time.time(),
                "accelerometer": (random.uniform(-0.5, 0.5), random.uniform(9.0, 10.0), random.uniform(-0.5, 0.5)),
                "gyroscope": (random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)),
                "magnetometer": (random.uniform(40, 50), random.uniform(20, 30), random.uniform(-10, 10))
            }
        
        try:
            # 数据格式通常为横向、纵向和垂直方向的值 (x, y, z)
            accel_data = accelerometer.acceleration
            gyro_data = gyroscope.rotation
            comp_data = compass.field 

            return {
                "timestamp": time.time(),
                "accelerometer": accel_data if accel_data else (0.0, 0.0, 0.0),
                "gyroscope": gyro_data if gyro_data else (0.0, 0.0, 0.0),
                "magnetometer": comp_data if comp_data else (0.0, 0.0, 0.0)
            }
        except Exception as e:
            print(f"读取传感器数据时出错: {e}")
            return None



import time
if __name__ == "__main__":
    collector = SensorDataCollector()
    collector.start_sensors()
    try:
        for _ in range(10):  # 抓取10次数据
            data = collector.collect_sensor_data()
            print(f"当前数据: {data}")
            time.sleep(1)    # 间隔1秒
    finally:
        collector.stop_sensors()

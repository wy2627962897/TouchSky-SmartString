import numpy as np

try:
    from filterpy.kalman import KalmanFilter
    FILTERPY_AVAILABLE = True
except ImportError:
    KalmanFilter = None
    FILTERPY_AVAILABLE = False

class SensorFusion:
    def __init__(self, dt=0.01):
        """
        初始化传感器数据融合与卡尔曼滤波器
        :param dt: 采样时间间隔，默认为10ms (100Hz)
        """
        self.dt = dt
        self.kf = None
        self.use_fallback_filter = not FILTERPY_AVAILABLE
        self.prev_smoothed = np.zeros(3)
        self.alpha = 0.25

        if self.use_fallback_filter:
            return

        self.kf = KalmanFilter(dim_x=6, dim_z=3)
        
        # 状态转移矩阵 F (6状态匀速模型: [x, y, z, vx, vy, vz])
        self.kf.F = np.array([[1, 0, 0, self.dt, 0, 0],
                              [0, 1, 0, 0, self.dt, 0],
                              [0, 0, 1, 0, 0, self.dt],
                              [0, 0, 0, 1, 0, 0],
                              [0, 0, 0, 0, 1, 0],
                              [0, 0, 0, 0, 0, 1]])
        
        # 观测矩阵 H (观测到的是直接的3D传感器值)
        self.kf.H = np.array([[1, 0, 0, 0, 0, 0],
                              [0, 1, 0, 0, 0, 0],
                              [0, 0, 1, 0, 0, 0]])
        
        # 初始状态协方差矩阵 P 
        self.kf.P *= 1000.
        
        # 观测噪声协方差矩阵 R
        self.kf.R = np.eye(3) * 0.1  
        
        # 过程噪声协方差矩阵 Q
        q_var = 0.01
        dt32 = (self.dt ** 3) / 2
        dt44 = (self.dt ** 4) / 4
        dt2  = self.dt ** 2
        
        self.kf.Q = np.array([
            [dt44, 0, 0, dt32, 0, 0],
            [0, dt44, 0, 0, dt32, 0],
            [0, 0, dt44, 0, 0, dt32],
            [dt32, 0, 0, dt2,  0, 0],
            [0, dt32, 0, 0, dt2,  0],
            [0, 0, dt32, 0, 0, dt2]
        ]) * q_var

    def normalize_data(self, raw_data):
        """
        传感器数据归一化
        """
        data = np.array(raw_data)
        # 例如将数据进行 Min-Max 缩放或者除以最大量程，这里保留原值作为基准
        # return data / MAX_RANGE
        return data

    def process_data(self, raw_data):
        """
        接收传感器数据，执行去噪平滑并提取时序数据特征
        :param raw_data: [x, y, z] 或类似形态数据
        :return: (smoothed_data, velocity/derivative)
        """
        if len(raw_data) != 3:
            raise ValueError("Expected 3D sensor data (e.g., [x, y, z]).")
            
        normalized = self.normalize_data(raw_data)
        
        # 卡尔曼滤波状态更新
        if self.use_fallback_filter:
            smoothed = self.alpha * normalized + (1.0 - self.alpha) * self.prev_smoothed
            derivative = (smoothed - self.prev_smoothed) / self.dt
            self.prev_smoothed = smoothed
            return smoothed, derivative

        self.kf.predict()
        self.kf.update(normalized)
        
        # 获得平滑后的信号极其一阶导数（变化率）
        smoothed = self.kf.x[:3].flatten()
        derivative = self.kf.x[3:].flatten()
        return smoothed, derivative

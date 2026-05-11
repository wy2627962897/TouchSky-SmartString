import unittest
import numpy as np
import sys
import os

# 将项目根目录加入到环境变量中，方便绝对引入
curr_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(curr_dir, '../'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.sensor_fusion.kalman_filter import SensorFusion

class TestSensorFusion(unittest.TestCase):
    def setUp(self):
        self.kf = SensorFusion(dt=0.01)

    def test_kalman_filter_initialization(self):
        self.assertEqual(self.kf.dt, 0.01)
        self.assertEqual(self.kf.kf.dim_x, 6)
        self.assertEqual(self.kf.kf.dim_z, 3)

    def test_process_data(self):
        # 模拟一个静态数据
        raw_data = [0.0, 0.0, 9.8]
        smoothed, derivative = self.kf.process_data(raw_data)
        
        self.assertEqual(len(smoothed), 3)
        self.assertEqual(len(derivative), 3)
        
        # 对于初始状态，平滑值应该接近输入值
        np.testing.assert_almost_equal(smoothed, raw_data, decimal=1)

if __name__ == '__main__':
    unittest.main()
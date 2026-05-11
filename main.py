import sys
import os

# 确保在 Android 等平台上时，能正确引用 src 下的模块
curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.append(curr_dir)

# 导入真正的 UI 主入口并启动
from src.app.ui_main import TouchSkyApp

if __name__ == '__main__':
    TouchSkyApp().run()
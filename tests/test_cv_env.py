import torch
print(f"PyTorch 版本: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")

import torchvision
print(f"TorchVision 版本: {torchvision.__version__}")

import ultralytics
print(f"Ultralytics 版本: {ultralytics.__version__}")

import numpy as np
print(f"NumPy 版本: {np.__version__}")
test_array = np.array([1, 2, 3, 4, 5])
print(f"测试数组: {test_array}")

import pandas as pd
print(f"Pandas 版本: {pd.__version__}")
test_df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
print(f"测试:\n{test_df}")


import cv2
print(f"OpenCV 版本: {cv2.__version__}")

import matplotlib
print(f"Matplotlib 版本: {matplotlib.__version__}")
import matplotlib.pyplot as plt
print("Matplotlib 后端:", plt.get_backend())


print("\nPyTorch CPU 张量运算...")
x = torch.rand(5, 3)
y = torch.rand(5, 3)
z = x + y
print(f"随机张量 x:\n{x}")
print(f"x + y 结果:\n{z}")

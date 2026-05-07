"""
集中式 UI 缩放工具（1920x1080 设计分辨率 + 等比缩放 letterbox）
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class UIScale:
    """UI 缩放辅助类"""

    design_width: int = 1920
    design_height: int = 1080
    window_width: int = 1920
    window_height: int = 1080
    scale: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0

    def __init__(self, window_width: int, window_height: int,
                 design_width: int = 1920, design_height: int = 1080):
        self.design_width = design_width
        self.design_height = design_height
        self.update(window_width, window_height)

    def update(self, window_width: int, window_height: int):
        """根据当前窗口尺寸更新缩放参数"""
        self.window_width = max(1, int(window_width))
        self.window_height = max(1, int(window_height))
        self.scale = min(
            self.window_width / self.design_width,
            self.window_height / self.design_height
        )
        self.offset_x = (self.window_width - self.design_width * self.scale) / 2
        self.offset_y = (self.window_height - self.design_height * self.scale) / 2

    def sx(self, x: float) -> float:
        """设计坐标 X -> 窗口像素 X"""
        return self.offset_x + x * self.scale

    def sy(self, y: float) -> float:
        """设计坐标 Y -> 窗口像素 Y"""
        return self.offset_y + y * self.scale

    def ss(self, size: float, min_value: int = 1) -> int:
        """设计尺寸 -> 缩放后像素尺寸"""
        return max(min_value, int(round(size * self.scale)))

    def rect(self, x: float, y: float, w: float, h: float) -> Tuple[float, float, float, float]:
        """设计矩形 -> 窗口矩形（x,y,w,h）"""
        return self.sx(x), self.sy(y), w * self.scale, h * self.scale

    def to_design(self, x: float, y: float) -> Tuple[float, float]:
        """窗口像素坐标 -> 设计坐标"""
        if self.scale <= 0:
            return x, y
        return (x - self.offset_x) / self.scale, (y - self.offset_y) / self.scale

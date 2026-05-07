"""
ui_scale.py — UI 缩放工具模块

统一处理高 DPI / 4K 屏幕下的 UI 自适应缩放。
设计分辨率: 1920×1080（参考基准）。

所有 UI 坐标、尺寸、字体都应通过本模块的辅助函数换算后再传给 arcade，
从而在 1080p / 2K / 4K（Windows 缩放 100%/150%/200%）下保持视觉一致。

用法示例::

    from ui_scale import S, update_scale

    # 在窗口初始化 / on_resize 时更新一次即可
    update_scale(window_width, window_height)

    # 在绘制时使用换算函数
    arcade.draw_text("Hello", S.px(100), S.py(50), color, S.font(24))
    arcade.draw_lrbt_rectangle_filled(
        S.px(20), S.px(470), S.py(30), S.py(250), color
    )

API 速查::

    S.px(x)        — 水平坐标或宽度（设计像素 → 实际像素）
    S.py(y)        — 垂直坐标或高度（设计像素 → 实际像素）
    S.font(size)   — 字体大小缩放（等比）
    S.scale(v)     — 等比缩放（圆半径、边框宽度等）
    S.rect(w, h)   — 返回 (scaled_w, scaled_h) 二元组
"""

# ─── 设计分辨率（基准） ──────────────────────────────────────────
DESIGN_WIDTH: int = 1920
DESIGN_HEIGHT: int = 1080


class UIScale:
    """UI 缩放计算器。

    根据"设计分辨率"与"实际窗口尺寸"计算缩放因子，
    并提供便捷方法把"设计像素"映射到"实际像素"。
    窗口大小变化时只需调用 :meth:`update` 即可刷新全部缩放系数。
    """

    def __init__(self, window_width: int = DESIGN_WIDTH,
                 window_height: int = DESIGN_HEIGHT) -> None:
        self.update(window_width, window_height)

    # ------------------------------------------------------------------ #
    def update(self, window_width: int, window_height: int) -> None:
        """更新窗口尺寸和缩放因子（应在 on_resize 中调用）。"""
        self.window_width: int = window_width
        self.window_height: int = window_height
        # 水平 / 垂直独立缩放因子
        self.sx: float = window_width / DESIGN_WIDTH
        self.sy: float = window_height / DESIGN_HEIGHT
        # 等比缩放因子（取较小值，保证内容不超出屏幕边界）
        self.s: float = min(self.sx, self.sy)

    # ─── 坐标 / 尺寸换算 ─────────────────────────────────────────── #
    def px(self, x: float) -> float:
        """水平坐标或宽度：设计像素 → 实际像素。"""
        return x * self.sx

    def py(self, y: float) -> float:
        """垂直坐标或高度：设计像素 → 实际像素。"""
        return y * self.sy

    def scale(self, value: float) -> float:
        """等比缩放（圆半径、边框宽度等需保持比例的场景）。"""
        return value * self.s

    def font(self, size: int) -> int:
        """字体大小缩放（等比，保证在宽屏/超宽屏下也不会过大）。"""
        return max(1, int(size * self.s))

    def rect(self, w: float, h: float):
        """矩形尺寸缩放，返回 ``(scaled_w, scaled_h)``。"""
        return self.px(w), self.py(h)


# ─── 模块级单例（全局共享）───────────────────────────────────────── #
# 初始值为设计分辨率（缩放系数均为 1.0）。
# 游戏启动后第一件事应调用 update_scale(w, h) 以得到正确的缩放系数；
# 每次 on_resize 也应再次调用。
S: UIScale = UIScale()


def update_scale(window_width: int, window_height: int) -> None:
    """更新全局缩放单例。在窗口初始化及 ``on_resize`` 中调用。"""
    S.update(window_width, window_height)

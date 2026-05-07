"""
背包UI渲染器模块
负责绘制背包界面和物品
"""
import arcade
from typing import Optional, Tuple
from inventory import Inventory, InventoryItem, ItemShape
from config import CONSTANTS
from ui_scale import S


class InventoryRenderer:
    """背包UI渲染器"""
    
    def __init__(self, window_width: int, window_height: int):
        self.window_width = window_width
        self.window_height = window_height
        
        # 背包显示状态
        self.inventory_visible = False
        self.current_inventory: Optional[Inventory] = None
        
        # 鼠标交互
        self.hovered_slot: Optional[Tuple[int, int]] = None
        self.hovered_item: Optional[InventoryItem] = None
        
        # 计算背包面板位置（居中）
        self._calculate_panel_position()
    
    def _calculate_panel_position(self):
        """计算背包面板的位置"""
        slot_size = S.scale(CONSTANTS.INVENTORY_SLOT_SIZE)
        padding = S.scale(CONSTANTS.INVENTORY_PADDING)
        grid_width = CONSTANTS.INVENTORY_WIDTH
        grid_height = CONSTANTS.INVENTORY_HEIGHT
        
        # 面板总尺寸
        panel_width = grid_width * slot_size + (grid_width + 1) * padding
        panel_height = grid_height * slot_size + (grid_height + 1) * padding + S.py(80)
        
        # 居中位置
        self.panel_x = (self.window_width - panel_width) // 2
        self.panel_y = (self.window_height - panel_height) // 2
        
        # 保存缩放后的尺寸供绘制用
        self._slot_size = slot_size
        self._padding = padding
        
        # 网格起始位置
        self.grid_start_x = self.panel_x + padding
        self.grid_start_y = self.panel_y + padding + S.py(60)  # 留出顶部空间
    
    def toggle_inventory(self, inventory: Inventory):
        """切换背包显示"""
        self.current_inventory = inventory
        self.inventory_visible = not self.inventory_visible
        
        if self.inventory_visible:
            self._calculate_panel_position()
    
    def close_inventory(self):
        """关闭背包"""
        self.inventory_visible = False
        self.hovered_slot = None
        self.hovered_item = None
    
    def is_visible(self) -> bool:
        """检查背包是否可见"""
        return self.inventory_visible
    
    def get_item_at_position(self, x: float, y: float):
        """
        根据屏幕坐标获取物品
        
        Args:
            x, y: 屏幕坐标
            
        Returns:
            InventoryItem 或 None
        """
        if not self.inventory_visible or not self.current_inventory:
            return None
        
        slot_size = getattr(self, '_slot_size', S.scale(CONSTANTS.INVENTORY_SLOT_SIZE))
        padding = getattr(self, '_padding', S.scale(CONSTANTS.INVENTORY_PADDING))
        
        # 遍历网格查找点击的物品
        for grid_y in range(self.current_inventory.grid_height):
            for grid_x in range(self.current_inventory.grid_width):
                slot_x = self.grid_start_x + grid_x * (slot_size + padding)
                slot_y = self.grid_start_y + grid_y * (slot_size + padding)
                
                # 检查是否在格子范围内
                if (slot_x <= x <= slot_x + slot_size and 
                    slot_y <= y <= slot_y + slot_size):
                    item = self.current_inventory.get_item_at(grid_x, grid_y)
                    if item:
                        return item
        
        return None
    
    def draw(self):
        """绘制背包界面"""
        if not self.inventory_visible or not self.current_inventory:
            return
        
        self._draw_background()
        self._draw_title()
        self._draw_status_bars()
        self._draw_grid()
        self._draw_items()
        self._draw_hover_tooltip()
    
    def _draw_background(self):
        """绘制背包背景"""
        slot_size = getattr(self, '_slot_size', S.scale(CONSTANTS.INVENTORY_SLOT_SIZE))
        padding = getattr(self, '_padding', S.scale(CONSTANTS.INVENTORY_PADDING))
        grid_width = CONSTANTS.INVENTORY_WIDTH
        grid_height = CONSTANTS.INVENTORY_HEIGHT
        
        panel_width = grid_width * slot_size + (grid_width + 1) * padding
        panel_height = grid_height * slot_size + (grid_height + 1) * padding + S.py(80)
        
        # 计算矩形的left, right, bottom, top
        left = self.panel_x
        right = self.panel_x + panel_width
        bottom = self.panel_y
        top = self.panel_y + panel_height
        
        # 半透明背景（使用RGBA格式）
        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top,
            (0, 0, 0, 200)  # 半透明黑色 RGBA
        )
        
        # 边框
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top,
            arcade.color.WHITE,
            border_width=3
        )
    
    def _draw_title(self):
        """绘制标题"""
        title_text = f"背包 - {self.current_inventory.owner_name}"
        arcade.draw_text(
            title_text,
            self.panel_x + getattr(self, '_padding', S.scale(CONSTANTS.INVENTORY_PADDING)),
            self.panel_y + S.py(40),
            arcade.color.WHITE,
            font_size=S.font(20),
            bold=True
        )
    
    def _draw_status_bars(self):
        """绘制状态条（体积和重量）"""
        info = self.current_inventory.get_usage_info()
        slot_size = getattr(self, '_slot_size', S.scale(CONSTANTS.INVENTORY_SLOT_SIZE))
        padding = getattr(self, '_padding', S.scale(CONSTANTS.INVENTORY_PADDING))
        grid_width = CONSTANTS.INVENTORY_WIDTH
        
        bar_y = self.panel_y + S.py(15)
        bar_width = (grid_width * slot_size + (grid_width + 1) * padding) // 2 - S.px(20)
        bar_height = S.py(15)
        
        # 体积条
        volume_x = self.panel_x + getattr(self, '_padding', S.scale(CONSTANTS.INVENTORY_PADDING)) + S.px(10)
        self._draw_status_bar(
            volume_x, bar_y, bar_width, bar_height,
            info['volume_used'], info['volume_max'],
            "体积", arcade.color.BLUE
        )
        
        # 重量条
        weight_x = volume_x + bar_width + 20
        self._draw_status_bar(
            weight_x, bar_y, bar_width, bar_height,
            info['weight_used'], info['weight_max'],
            "重量", arcade.color.ORANGE
        )
    
    def _draw_status_bar(self, x: int, y: int, width: int, height: int, 
                        current: float, maximum: float, label: str, color: Tuple[int, int, int]):
        """绘制单个状态条"""
        # 计算矩形边界
        left = x
        right = x + width
        bottom = y
        top = y + height
        
        # 背景
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.DARK_GRAY)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, arcade.color.WHITE, border_width=1)
        
        # 填充
        if maximum > 0:
            fill_width = max(0, min(width * (current / maximum), width))
            fill_right = x + fill_width
            arcade.draw_lrbt_rectangle_filled(
                x, fill_right, y + 1, y + height - 1,
                color
            )
        
        # 文字
        text = f"{label}: {current:.1f}/{maximum:.1f}"
        arcade.draw_text(
            text, x + S.px(5), y + S.py(2),
            arcade.color.WHITE,
            font_size=S.font(10)
        )
    
    def _draw_grid(self):
        """绘制背包网格"""
        slot_size = getattr(self, '_slot_size', S.scale(CONSTANTS.INVENTORY_SLOT_SIZE))
        padding = getattr(self, '_padding', S.scale(CONSTANTS.INVENTORY_PADDING))
        
        for y in range(self.current_inventory.grid_height):
            for x in range(self.current_inventory.grid_width):
                slot_x = self.grid_start_x + x * (slot_size + padding)
                slot_y = self.grid_start_y + y * (slot_size + padding)
                
                # 格子背景
                if self.hovered_slot == (x, y):
                    color = arcade.color.LIGHT_GRAY
                else:
                    color = arcade.color.GRAY
                
                # 计算格子边界
                left = slot_x
                right = slot_x + slot_size
                bottom = slot_y
                top = slot_y + slot_size
                
                arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, color)
                
                # 格子边框
                arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, arcade.color.WHITE, border_width=1)
    
    def _draw_items(self):
        """绘制所有物品"""
        slot_size = getattr(self, '_slot_size', S.scale(CONSTANTS.INVENTORY_SLOT_SIZE))
        padding = getattr(self, '_padding', S.scale(CONSTANTS.INVENTORY_PADDING))
        
        for item in self.current_inventory.items:
            # 找到物品在网格中的位置
            position = self._find_item_position(item)
            if position is None:
                continue
            
            x, y = position
            slot_x = self.grid_start_x + x * (slot_size + padding)
            slot_y = self.grid_start_y + y * (slot_size + padding)
            
            # 根据形状绘制物品
            self._draw_item_at(item, slot_x, slot_y, slot_size, padding)
    
    def _draw_item_at(self, item: InventoryItem, x: int, y: int, slot_size: int, padding: int):
        """在指定位置绘制物品"""
        # 获取物品占据的格子数
        width_slots, height_slots = self._get_item_dimensions(item.shape)
        
        # 计算实际尺寸
        actual_width = width_slots * slot_size + (width_slots - 1) * padding
        actual_height = height_slots * slot_size + (height_slots - 1) * padding
        
        # 计算矩形边界
        left = x
        right = x + actual_width
        bottom = y
        top = y + actual_height
        
        # 绘制物品背景
        # 将RGB转换为RGBA（添加透明度）
        item_color_rgba = (*item.icon_color, 200)
        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top,
            item_color_rgba
        )
        
        # 绘制边框
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top,
            arcade.color.WHITE,
            border_width=2
        )
        
        # 绘制物品名称（如果空间足够）
        if actual_width > S.px(40) and actual_height > S.py(40):
            display_name = item.name[:6] if len(item.name) > 6 else item.name
            if item.stackable and item.stack_count > 1:
                display_name += f"x{item.stack_count}"
            
            font_size = max(S.font(8), min(S.font(12), int(actual_width // len(display_name))))
            arcade.draw_text(
                display_name,
                x + actual_width // 2, y + actual_height // 2,
                arcade.color.WHITE,
                font_size=font_size,
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
    
    def _draw_hover_tooltip(self):
        """绘制悬停提示"""
        if not self.hovered_item:
            return
        
        # 获取鼠标位置（这里简化处理，实际需要跟踪鼠标）
        # 在实际实现中，需要从InputHandler获取鼠标位置
        
        tooltip_text = [
            self.hovered_item.name,
            f"类型: {self.hovered_item.item_type.value}",
            f"重量: {self.hovered_item.weight:.1f}",
            f"体积: {self.hovered_item.volume}",
        ]
        
        if self.hovered_item.description:
            tooltip_text.append("")
            tooltip_text.append(self.hovered_item.description)
        
        # 绘制提示框（暂时不实现，需要鼠标位置）
        pass
    
    def _find_item_position(self, item: InventoryItem) -> Optional[Tuple[int, int]]:
        """查找物品在网格中的位置"""
        for y in range(self.current_inventory.grid_height):
            for x in range(self.current_inventory.grid_width):
                if self.current_inventory.grid[y][x] == item:
                    return (x, y)
        return None
    
    def _get_item_dimensions(self, shape: ItemShape) -> Tuple[int, int]:
        """获取物品形状的宽度和高度（以格子为单位）"""
        dimensions = {
            ItemShape.SINGLE: (1, 1),
            ItemShape.HORIZONTAL_2: (2, 1),
            ItemShape.VERTICAL_2: (1, 2),
            ItemShape.SQUARE_2X2: (2, 2),
            ItemShape.HORIZONTAL_3: (3, 1),
            ItemShape.L_SHAPE: (2, 2),
        }
        return dimensions.get(shape, (1, 1))
    
    def get_slot_at_screen_pos(self, screen_x: float, screen_y: float) -> Optional[Tuple[int, int]]:
        """根据屏幕坐标获取格子坐标"""
        if not self.inventory_visible:
            return None
        
        slot_size = CONSTANTS.INVENTORY_SLOT_SIZE
        padding = CONSTANTS.INVENTORY_PADDING
        
        # 转换为网格坐标
        rel_x = screen_x - self.grid_start_x
        rel_y = screen_y - self.grid_start_y
        
        if rel_x < 0 or rel_y < 0:
            return None
        
        grid_x = int(rel_x // (slot_size + padding))
        grid_y = int(rel_y // (slot_size + padding))
        
        # 检查是否在有效范围内
        if (0 <= grid_x < self.current_inventory.grid_width and 
            0 <= grid_y < self.current_inventory.grid_height):
            return (grid_x, grid_y)
        
        return None
    
    def update_hover(self, mouse_x: float, mouse_y: float):
        """更新悬停状态"""
        if not self.inventory_visible:
            self.hovered_slot = None
            self.hovered_item = None
            return
        
        slot_pos = self.get_slot_at_screen_pos(mouse_x, mouse_y)
        self.hovered_slot = slot_pos
        
        if slot_pos:
            x, y = slot_pos
            self.hovered_item = self.current_inventory.get_item_at(x, y)
        else:
            self.hovered_item = None

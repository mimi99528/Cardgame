"""
生命骰回血选择视图
战斗结束后，为每个存活的队友提供使用生命骰回血的UI界面
"""
import arcade
from typing import List, Optional, Callable
from ui_scale import S


class HitDiceRecoveryView(arcade.View):
    """生命骰回血选择视图"""
    
    def __init__(self, recovery_queue: list, on_complete: Callable):
        super().__init__()
        
        self.recovery_queue = recovery_queue  # 需要回血的实体列表
        self.on_complete = on_complete  # 完成回调
        
        # 当前处理的实体索引
        self.current_index = 0
        
        # UI元素位置
        self.window_width = arcade.get_window().width if arcade.get_window() else 1920
        self.window_height = arcade.get_window().height if arcade.get_window() else 1080
        
        # 选择的骰子数量（初始为0）
        self.selected_dice = 0
        
        # 按钮区域
        self.confirm_button_rect = None
        self.dice_buttons = []  # [(x, y, width, height, dice_count), ...]
        
        # 计算面板位置
        self._calculate_panel_position()
    
    def _calculate_panel_position(self):
        """计算面板位置"""
        # 面板尺寸
        self.panel_width = S.px(600)
        self.panel_height = S.py(400)
        
        # 居中显示
        self.panel_x = (self.window_width - self.panel_width) // 2
        self.panel_y = (self.window_height - self.panel_height) // 2
        
        # 按钮区域
        button_y = self.panel_y + S.py(80)
        button_spacing = S.px(120)
        start_x = self.panel_x + (self.panel_width - (5 * button_spacing)) // 2
        
        # 创建0-5个骰子的按钮（最多等级数，但不超过5个以便显示）
        current_entity = self.recovery_queue[self.current_index]['entity']
        max_dice = min(current_entity.level, 5)
        
        self.dice_buttons.clear()
        for i in range(max_dice + 1):  # 0到max_dice
            x = start_x + i * button_spacing
            width = S.px(100)
            height = S.py(60)
            self.dice_buttons.append((x, button_y, width, height, i))
        
        # 确定按钮
        confirm_width = S.px(150)
        confirm_height = S.py(50)
        confirm_x = self.panel_x + (self.panel_width - confirm_width) // 2
        confirm_y = self.panel_y + S.py(30)
        self.confirm_button_rect = (confirm_x, confirm_y, confirm_width, confirm_height)
    
    def on_draw(self):
        """绘制界面"""
        self.clear()
        
        # 绘制背景遮罩
        overlay_color = (0, 0, 0, 180)
        arcade.draw_lrbt_rectangle_filled(
            0, self.window_width, 0, self.window_height,
            overlay_color
        )
        
        # 绘制主面板
        panel_color = (40, 40, 60, 230)
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y, self.panel_y + self.panel_height,
            panel_color
        )
        
        # 绘制面板边框
        arcade.draw_lrbt_rectangle_outline(
            self.panel_x, self.panel_x + self.panel_width,
            self.panel_y, self.panel_y + self.panel_height,
            arcade.color.WHITE,
            border_width=3
        )
        
        # 获取当前实体信息
        current_data = self.recovery_queue[self.current_index]
        entity = current_data['entity']
        
        # 绘制标题
        title_text = f"{current_data['name']} - 生命骰恢复"
        title_x = self.panel_x + self.panel_width // 2
        title_y = self.panel_y + self.panel_height - S.py(40)
        
        arcade.draw_text(
            title_text,
            title_x, title_y,
            arcade.color.GOLD,
            S.font(28),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # 绘制状态信息
        status_y = self.panel_y + self.panel_height - S.py(100)
        hp_text = f"当前HP: {current_data['current_hp']}/{current_data['max_hp']}"
        dice_text = f"生命骰: {current_data['current_hit_dice']}/{current_data['max_hit_dice']} (d{current_data['hit_dice_type']})"
        
        arcade.draw_text(
            hp_text,
            self.panel_x + S.px(30), status_y,
            arcade.color.WHITE,
            S.font(20),
            anchor_x="left",
            anchor_y="center"
        )
        
        arcade.draw_text(
            dice_text,
            self.panel_x + S.px(30), status_y - S.py(40),
            arcade.color.WHITE,
            S.font(20),
            anchor_x="left",
            anchor_y="center"
        )
        
        # 绘制提示文本
        hint_text = "选择要使用的生命骰数量："
        hint_x = self.panel_x + self.panel_width // 2
        hint_y = self.panel_y + S.py(180)
        
        arcade.draw_text(
            hint_text,
            hint_x, hint_y,
            arcade.color.YELLOW,
            S.font(18),
            anchor_x="center",
            anchor_y="center"
        )
        
        # 绘制骰子选择按钮
        for x, y, width, height, dice_count in self.dice_buttons:
            # 根据是否选中设置颜色
            if dice_count == self.selected_dice:
                button_color = (100, 150, 255, 200)  # 选中状态
                border_color = arcade.color.YELLOW
            else:
                button_color = (60, 60, 80, 200)  # 未选中状态
                border_color = arcade.color.WHITE
            
            # 绘制按钮背景
            arcade.draw_lrbt_rectangle_filled(x, x + width, y, y + height, button_color)
            
            # 绘制按钮边框
            arcade.draw_lrbt_rectangle_outline(x, x + width, y, y + height, border_color, border_width=2)
            
            # 绘制按钮文字
            if dice_count == 0:
                label = "跳过"
            else:
                label = f"{dice_count}个"
            
            arcade.draw_text(
                label,
                x + width // 2, y + height // 2,
                arcade.color.WHITE,
                S.font(18),
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
        
        # 绘制预计回血量（如果选择了骰子）
        if self.selected_dice > 0:
            # 估算回血量（平均值）
            avg_per_die = (current_data['hit_dice_type'] + 1) / 2
            estimated_heal = int(self.selected_dice * avg_per_die)
            max_possible_heal = min(estimated_heal, current_data['max_hp'] - current_data['current_hp'])
            
            estimate_text = f"预计恢复: ~{estimated_heal} HP (最多{max_possible_heal})"
            estimate_x = self.panel_x + self.panel_width // 2
            estimate_y = self.panel_y + S.py(130)
            
            arcade.draw_text(
                estimate_text,
                estimate_x, estimate_y,
                arcade.color.GREEN,
                S.font(16),
                anchor_x="center",
                anchor_y="center"
            )
        
        # 绘制确定按钮
        confirm_x, confirm_y, confirm_width, confirm_height = self.confirm_button_rect
        arcade.draw_lrbt_rectangle_filled(
            confirm_x, confirm_x + confirm_width,
            confirm_y, confirm_y + confirm_height,
            (50, 150, 50, 200)
        )
        arcade.draw_lrbt_rectangle_outline(
            confirm_x, confirm_x + confirm_width,
            confirm_y, confirm_y + confirm_height,
            arcade.color.WHITE,
            border_width=2
        )
        
        arcade.draw_text(
            "确定",
            confirm_x + confirm_width // 2,
            confirm_y + confirm_height // 2,
            arcade.color.WHITE,
            S.font(22),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # 绘制进度指示
        progress_text = f"({self.current_index + 1}/{len(self.recovery_queue)})"
        arcade.draw_text(
            progress_text,
            self.panel_x + self.panel_width - S.px(20),
            self.panel_y + self.panel_height - S.py(20),
            arcade.color.GRAY,
            S.font(14),
            anchor_x="right",
            anchor_y="bottom"
        )
    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """鼠标点击事件"""
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
        
        # 检查是否点击了骰子选择按钮
        for btn_x, btn_y, btn_width, btn_height, dice_count in self.dice_buttons:
            if (btn_x <= x <= btn_x + btn_width and 
                btn_y <= y <= btn_y + btn_height):
                self.selected_dice = dice_count
                return
        
        # 检查是否点击了确定按钮
        confirm_x, confirm_y, confirm_width, confirm_height = self.confirm_button_rect
        if (confirm_x <= x <= confirm_x + confirm_width and 
            confirm_y <= y <= confirm_y + confirm_height):
            self._confirm_selection()
    
    def _confirm_selection(self):
        """确认选择"""
        current_data = self.recovery_queue[self.current_index]
        entity = current_data['entity']
        
        healed_amount = 0
        if self.selected_dice > 0:
            # 实际使用生命骰
            healed_amount = entity.use_hit_dice(self.selected_dice)
            
            # 记录日志
            from battle_system import BattleLog
            log_msg = f"\n{entity.name} 使用了 {self.selected_dice} 个生命骰 (d{entity.hit_dice_type})，恢复了 {healed_amount} 点HP！"
            print(log_msg)
            print(f"  当前HP: {entity.hp}/{entity.max_hp}, 剩余生命骰: {entity.current_hit_dice}/{entity.max_hit_dice}")
        
        # 移动到下一个实体
        self.current_index += 1
        
        # 检查是否所有实体都处理完毕
        if self.current_index >= len(self.recovery_queue):
            # 所有实体处理完毕，返回游戏视图
            self.on_complete()
            window = arcade.get_window()
            if hasattr(window, '_game_view') and window._game_view:
                window.show_view(window._game_view)
        else:
            # 重置选择，处理下一个实体
            self.selected_dice = 0
            self._calculate_panel_position()
    
    def on_resize(self, width: int, height: int):
        """窗口尺寸变化时更新"""
        self.window_width = width
        self.window_height = height
        self._calculate_panel_position()

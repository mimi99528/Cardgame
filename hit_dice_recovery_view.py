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
        
        # 滑动条相关
        self.slider_rect = None  # (x, y, width, height)
        self.slider_thumb_x = 0  # 滑块当前位置
        self.is_dragging_slider = False  # 是否正在拖动滑块
        
        # 输入框相关
        self.input_rect = None  # (x, y, width, height)
        self.input_text = "0"  # 输入框文本
        self.is_input_active = False  # 输入框是否激活
        self.input_cursor_visible = True  # 光标是否可见
        self.input_cursor_timer = 0  # 光标闪烁计时器
        
        # 按钮区域
        self.confirm_button_rect = None
        self.dice_buttons = []  # [(x, y, width, height, dice_count), ...]
        
        # 计算面板位置
        self._calculate_panel_position()
    
    def _update_slider_position(self):
        """根据 selected_dice 更新滑块位置"""
        if not self.slider_rect or self.max_dice == 0:
            return
        
        slider_x, slider_y, slider_width, slider_height = self.slider_rect
        # 计算滑块位置（0到max_dice之间）
        ratio = self.selected_dice / self.max_dice if self.max_dice > 0 else 0
        self.slider_thumb_x = slider_x + ratio * slider_width
    
    def _update_selected_dice_from_slider(self, mouse_x: float):
        """根据鼠标位置更新选中的骰子数量"""
        if not self.slider_rect or self.max_dice == 0:
            return
        
        slider_x, slider_y, slider_width, slider_height = self.slider_rect
        # 限制鼠标位置在滑动条范围内
        clamped_x = max(slider_x, min(mouse_x, slider_x + slider_width))
        # 计算比例并转换为整数
        ratio = (clamped_x - slider_x) / slider_width
        new_dice = round(ratio * self.max_dice)
        
        if new_dice != self.selected_dice:
            self.selected_dice = new_dice
            self.input_text = str(self.selected_dice)
            self._update_slider_position()
    
    def _validate_input(self):
        """验证并应用输入框的值"""
        try:
            value = int(self.input_text)
            # 限制在有效范围内
            value = max(0, min(value, self.max_dice))
            self.selected_dice = value
            self._update_slider_position()
        except ValueError:
            # 如果输入无效，恢复为当前选中的值
            self.input_text = str(self.selected_dice)
    
    def _calculate_panel_position(self):
        # 面板尺寸
        self.panel_width = S.px(600)
        self.panel_height = S.py(450)  # 增加高度以容纳滑动条和输入框
        
        # 居中显示
        self.panel_x = (self.window_width - self.panel_width) // 2
        self.panel_y = (self.window_height - self.panel_height) // 2
        
        # 获取当前实体信息
        current_entity = self.recovery_queue[self.current_index]['entity']
        max_dice = min(current_entity.current_hit_dice, current_entity.level)
        self.max_dice = max_dice  # 保存最大值供其他方法使用
        
        # 滑动条区域（在提示文本下方）
        slider_y = self.panel_y + S.py(140)
        slider_width = S.px(400)
        slider_height = S.py(30)
        slider_x = self.panel_x + (self.panel_width - slider_width) // 2
        self.slider_rect = (slider_x, slider_y, slider_width, slider_height)
        
        # 初始化滑块位置
        self._update_slider_position()
        
        # 输入框区域（在滑动条右侧）
        input_width = S.px(80)
        input_height = S.py(35)
        input_x = slider_x + slider_width + S.px(20)
        input_y = slider_y
        self.input_rect = (input_x, input_y, input_width, input_height)
        
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
        
        # 绘制滑动条背景
        if self.slider_rect:
            slider_x, slider_y, slider_width, slider_height = self.slider_rect
            # 背景轨道
            arcade.draw_lrbt_rectangle_filled(
                slider_x, slider_x + slider_width,
                slider_y, slider_y + slider_height,
                (80, 80, 100, 200)
            )
            arcade.draw_lrbt_rectangle_outline(
                slider_x, slider_x + slider_width,
                slider_y, slider_y + slider_height,
                arcade.color.WHITE,
                border_width=2
            )
            
            # 已填充部分
            if self.selected_dice > 0 and self.max_dice > 0:
                fill_ratio = self.selected_dice / self.max_dice
                fill_width = slider_width * fill_ratio
                arcade.draw_lrbt_rectangle_filled(
                    slider_x, slider_x + fill_width,
                    slider_y, slider_y + slider_height,
                    (100, 150, 255, 200)
                )
            
            # 滑块
            thumb_size = S.py(35)
            thumb_x = self.slider_thumb_x - thumb_size // 2
            arcade.draw_lrbt_rectangle_filled(
                thumb_x, thumb_x + thumb_size,
                slider_y - S.py(5), slider_y + slider_height + S.py(5),
                (150, 200, 255, 230)
            )
            arcade.draw_lrbt_rectangle_outline(
                thumb_x, thumb_x + thumb_size,
                slider_y - S.py(5), slider_y + slider_height + S.py(5),
                arcade.color.WHITE,
                border_width=2
            )
            
            # 最小值和最大值标签
            arcade.draw_text(
                "0",
                slider_x, slider_y - S.py(25),
                arcade.color.GRAY,
                S.font(14),
                anchor_x="center",
                anchor_y="center"
            )
            arcade.draw_text(
                str(self.max_dice),
                slider_x + slider_width, slider_y - S.py(25),
                arcade.color.GRAY,
                S.font(14),
                anchor_x="center",
                anchor_y="center"
            )
        
        # 绘制输入框
        if self.input_rect:
            input_x, input_y, input_width, input_height = self.input_rect
            
            # 输入框背景
            if self.is_input_active:
                input_color = (60, 60, 100, 220)
                border_color = arcade.color.YELLOW
            else:
                input_color = (50, 50, 70, 200)
                border_color = arcade.color.WHITE
            
            arcade.draw_lrbt_rectangle_filled(
                input_x, input_x + input_width,
                input_y, input_y + input_height,
                input_color
            )
            arcade.draw_lrbt_rectangle_outline(
                input_x, input_x + input_width,
                input_y, input_y + input_height,
                border_color,
                border_width=2
            )
            
            # 输入框文字
            display_text = self.input_text
            if self.is_input_active and self.input_cursor_visible:
                display_text += "|"  # 显示光标
            
            arcade.draw_text(
                display_text,
                input_x + input_width // 2,
                input_y + input_height // 2,
                arcade.color.WHITE,
                S.font(20),
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
            
            # 输入框标签
            arcade.draw_text(
                "数量",
                input_x + input_width // 2,
                input_y + input_height + S.py(15),
                arcade.color.GRAY,
                S.font(14),
                anchor_x="center",
                anchor_y="center"
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
        
        # 检查是否点击了滑动条
        if self.slider_rect:
            slider_x, slider_y, slider_width, slider_height = self.slider_rect
            # 扩大点击区域以便于点击
            expand = S.py(10)
            if (slider_x - expand <= x <= slider_x + slider_width + expand and 
                slider_y - expand <= y <= slider_y + slider_height + expand):
                self.is_dragging_slider = True
                self._update_selected_dice_from_slider(x)
                return
        
        # 检查是否点击了输入框
        if self.input_rect:
            input_x, input_y, input_width, input_height = self.input_rect
            if (input_x <= x <= input_x + input_width and 
                input_y <= y <= input_y + input_height):
                self.is_input_active = True
                self.input_cursor_visible = True
                self.input_cursor_timer = 0
                # 全选文本
                self.input_text = str(self.selected_dice)
                return
        
        # 点击其他地方取消输入框激活
        if self.is_input_active:
            self._validate_input()
            self.is_input_active = False
        
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
            # on_complete() 回调已经处理了视图切换（调用 _show_deck_edit()），无需再次 show_view
        else:
            # 重置选择，处理下一个实体
            self.selected_dice = 0
            self._calculate_panel_position()
    
    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, buttons: int, modifiers: int):
        """鼠标拖动事件"""
        if self.is_dragging_slider:
            self._update_selected_dice_from_slider(x)
    
    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        """鼠标释放事件"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.is_dragging_slider = False
    
    def on_key_press(self, key: int, modifiers: int):
        """键盘按下事件"""
        if self.is_input_active:
            if key == arcade.key.ENTER:
                # 确认输入
                self._validate_input()
                self.is_input_active = False
            elif key == arcade.key.ESCAPE:
                # 取消输入
                self.input_text = str(self.selected_dice)
                self.is_input_active = False
            elif key == arcade.key.BACKSPACE:
                # 删除最后一个字符
                if self.input_text:
                    self.input_text = self.input_text[:-1]
            # 数字键处理在 on_text 中处理
    
    def on_text(self, text: str):
        """文本输入事件"""
        if self.is_input_active:
            # 只允许数字
            if text.isdigit():
                self.input_text += text
                # 限制最大长度
                if len(self.input_text) > 3:
                    self.input_text = self.input_text[:3]
    
    def on_update(self, delta_time: float):
        """更新逻辑"""
        # 光标闪烁
        if self.is_input_active:
            self.input_cursor_timer += delta_time
            if self.input_cursor_timer > 0.5:  # 每0.5秒切换一次
                self.input_cursor_visible = not self.input_cursor_visible
                self.input_cursor_timer = 0
    
    def on_resize(self, width: int, height: int):
        """窗口尺寸变化时更新"""
        self.window_width = width
        self.window_height = height
        self._calculate_panel_position()

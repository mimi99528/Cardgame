"""
叙事场景UI渲染器模块
负责绘制叙事节点视图（60%窗口大小，半透明背景等）
"""
import arcade
from typing import List, Optional, Dict, Tuple
from models import Entity, Card
from narrative_system import NarrativeNode, NarrativeAction, NarrativeResult
from ui_scale import S
from chinese_text_helper import prepare_text_for_arcade


class NarrativeSceneRenderer:
    """叙事场景渲染器 - 处理叙事节点的UI显示"""
    
    def __init__(self, window_width: int, window_height: int):
        self.window_width = window_width
        self.window_height = window_height
        
        # 字体大小
        self.title_font_size = S.font(28)
        self.description_font_size = S.font(16)
        self.option_font_size = S.font(14)
        self.result_font_size = S.font(15)
        
        # 当前显示的节点
        self.current_node: Optional[NarrativeNode] = None
        
        # 玩家实体（用于检定）
        self.player_entity: Optional[Entity] = None
        
        # 已揭示的隐藏动作（通过拖入卡牌触发）
        self.revealed_hidden_actions: List[str] = []
        
        # 当前选中的动作和结果
        self.selected_action: Optional[NarrativeAction] = None
        self.current_result: Optional[NarrativeResult] = None
        
        # 按钮区域（用于点击检测）
        self.option_buttons: List[Dict] = []
        self.confirm_button: Optional[Dict] = None
    
    def on_resize(self, width: int, height: int):
        """窗口尺寸变化时更新"""
        self.window_width = width
        self.window_height = height
        self.title_font_size = S.font(28)
        self.description_font_size = S.font(16)
        self.option_font_size = S.font(14)
        self.result_font_size = S.font(15)
    
    def set_node(self, node: NarrativeNode, player: Entity):
        """设置当前显示的节点"""
        self.current_node = node
        self.player_entity = player
        self.selected_action = None
        self.current_result = None
        self.option_buttons.clear()
        self.confirm_button = None
    
    def reveal_hidden_action(self, action_name: str):
        """揭示隐藏动作（当玩家拖入对应卡牌时）"""
        if action_name not in self.revealed_hidden_actions:
            self.revealed_hidden_actions.append(action_name)
    
    def draw(self):
        """绘制叙事场景视图"""
        if not self.current_node:
            return
        
        # 计算视图尺寸（占窗口60%）
        view_width = int(self.window_width * 0.6)
        view_height = int(self.window_height * 0.7)
        view_x = (self.window_width - view_width) // 2
        view_y = (self.window_height - view_height) // 2
        
        # 绘制半透明黑色背景
        overlay_color = (0, 0, 0, 180)
        arcade.draw_lrbt_rectangle_filled(
            view_x, view_x + view_width,
            view_y, view_y + view_height,
            overlay_color
        )
        
        # 绘制白色边框
        arcade.draw_lrbt_rectangle_outline(
            view_x, view_x + view_width,
            view_y, view_y + view_height,
            arcade.color.WHITE, 3
        )
        
        # 如果有场景图片，在左侧绘制
        if self.current_node.scene_image:
            image_width = view_width // 2 - S.px(20)
            image_height = view_height // 2
            image_x = view_x + S.px(20)
            image_y = view_y + view_height - image_height - S.py(20)
            
            try:
                texture = arcade.load_texture(self.current_node.scene_image)
                arcade.draw_texture_rectangle(
                    image_x + image_width // 2,
                    image_y + image_height // 2,
                    image_width,
                    image_height,
                    texture
                )
            except Exception as e:
                print(f"警告：无法加载场景图片 {self.current_node.scene_image}: {e}")
        
        # 绘制标题（右侧上侧，大号字体）
        title_x = view_x + view_width // 2 + S.px(20)
        title_y = view_y + view_height - S.py(30)
        
        # 绘制标题（使用 Text 对象以支持更复杂的渲染或后续交互）
        # 对标题文本进行ZWSP处理以支持换行
        processed_title = prepare_text_for_arcade(
            self.current_node.title,
            max_width=view_width // 2 - S.px(40),
            font_size=self.title_font_size
        )
        title_text = arcade.Text(
            processed_title,
            title_x, title_y,
            arcade.color.GOLD,
            self.title_font_size,
            anchor_x="left",
            anchor_y="top",
            bold=True,
            multiline=True,
            width=int(view_width // 2 - S.px(40))
        )
        title_text.draw()
        
        # 绘制描述（标题下方，使用 Text 对象）
        desc_x = title_x
        desc_y = title_y - S.py(50)
        desc_width = view_width // 2 - S.px(60)  # 增加边距，确保文本不会太宽
        
        # 对描述文本进行ZWSP处理以支持换行
        processed_desc = prepare_text_for_arcade(
            self.current_node.description,
            max_width=int(desc_width),
            font_size=self.description_font_size
        )
        
        desc_text = arcade.Text(
            processed_desc,
            desc_x, desc_y,
            arcade.color.WHITE,
            self.description_font_size,
            anchor_x="left",
            anchor_y="top",
            multiline=True,
            width=int(desc_width),  # 设置最大宽度以启用自动换行
        )
        desc_text.draw()
        
        # 如果没有选择动作，显示选项列表
        if not self.selected_action:
            self._draw_options(view_x, view_y, view_width, view_height)
        else:
            # 显示检定结果
            self._draw_result(view_x, view_y, view_width, view_height)
    
    def _draw_options(self, view_x: int, view_y: int, view_width: int, view_height: int):
        """绘制选项列表"""
        self.option_buttons.clear()
        
        options_start_y = view_y + S.py(20)
        option_height = S.py(40)
        option_spacing = S.py(10)
        option_width = view_width - S.px(40)
        option_x = view_x + S.px(20)
        
        visible_options = []
        
        # 收集可见的选项
        for action in self.current_node.actions:
            if action.is_hidden and action.name not in self.revealed_hidden_actions:
                continue  # 跳过未揭示的隐藏选项
            visible_options.append(action)
        
        # 绘制每个选项
        for i, action in enumerate(visible_options):
            y_pos = options_start_y + i * (option_height + option_spacing)
            
            # 检查是否超出视图范围
            if y_pos + option_height > view_y + view_height - S.py(20):
                break
            
            # 绘制选项背景
            button_rect = {
                "left": option_x,
                "right": option_x + option_width,
                "bottom": y_pos,
                "top": y_pos + option_height,
                "action": action
            }
            self.option_buttons.append(button_rect)
            
            # 根据是否有检定添加颜色标识
            if action.check_type:
                bg_color = (100, 100, 150, 200)  # 需要检定的选项用蓝色调
            else:
                bg_color = (100, 100, 100, 200)  # 无需检定的选项用灰色调
            
            arcade.draw_lrbt_rectangle_filled(
                button_rect["left"], button_rect["right"],
                button_rect["bottom"], button_rect["top"],
                bg_color
            )
            
            # 绘制边框
            arcade.draw_lrbt_rectangle_outline(
                button_rect["left"], button_rect["right"],
                button_rect["bottom"], button_rect["top"],
                arcade.color.WHITE, 2
            )
            
            # 绘制选项文本
            option_text = f"[{action.name}]"
            
            # 如果有检定信息，添加到描述中
            if action.check_type and action.difficulty:
                dn = action.get_dn()
                check_info = f"（{action.check_type.value}，{action.difficulty.value}，DN{dn}）"
                option_text += f" {check_info}"
            
            # 添加描述
            full_text = f"{option_text} {action.description}"
            
            # 对选项文本进行ZWSP处理以支持换行
            processed_option = prepare_text_for_arcade(
                full_text,
                max_width=option_width - S.px(20),
                font_size=self.option_font_size
            )
            
            arcade.draw_text(
                processed_option,
                option_x + S.px(10),
                y_pos + option_height // 2,
                arcade.color.WHITE,
                self.option_font_size,
                anchor_x="left",
                anchor_y="center",
                multiline=True,
                width=int(option_width - S.px(20))
            )
    
    def _draw_result(self, view_x: int, view_y: int, view_width: int, view_height: int):
        """绘制检定结果"""
        if not self.current_result:
            return
        
        # 结果显示区域
        result_area_y = view_y + S.py(80)
        result_area_height = view_height - S.py(120)
        result_area_width = view_width - S.px(40)
        result_area_x = view_x + S.px(20)
        
        # 绘制结果背景
        arcade.draw_lrbt_rectangle_filled(
            result_area_x, result_area_x + result_area_width,
            result_area_y, result_area_y + result_area_height,
            (50, 50, 50, 220)
        )
        
        arcade.draw_lrbt_rectangle_outline(
            result_area_x, result_area_x + result_area_width,
            result_area_y, result_area_y + result_area_height,
            arcade.color.GOLD, 2
        )
        
        # 绘制结果文本
        result_text_y = result_area_y + result_area_height - S.py(20)
        
        # 对结果文本进行ZWSP处理以支持换行
        processed_result = prepare_text_for_arcade(
            self.current_result.text,
            max_width=result_area_width - S.px(20),
            font_size=self.result_font_size
        )
        
        arcade.draw_text(
            processed_result,
            result_area_x + S.px(10),
            result_text_y,
            arcade.color.WHITE,
            self.result_font_size,
            anchor_x="left",
            anchor_y="top",
            multiline=True,
            width=result_area_width - S.px(20)
        )
        
        # 绘制确定按钮
        self._draw_confirm_button(view_x, view_y, view_width, view_height)
    
    def _draw_confirm_button(self, view_x: int, view_y: int, view_width: int, view_height: int):
        """绘制确定按钮"""
        button_width = S.px(120)
        button_height = S.py(40)
        button_x = view_x + (view_width - button_width) // 2
        button_y = view_y + S.py(20)
        
        self.confirm_button = {
            "left": button_x,
            "right": button_x + button_width,
            "bottom": button_y,
            "top": button_y + button_height
        }
        
        # 绘制按钮背景
        arcade.draw_lrbt_rectangle_filled(
            button_x, button_x + button_width,
            button_y, button_y + button_height,
            arcade.color.DARK_GREEN
        )
        
        # 绘制按钮边框
        arcade.draw_lrbt_rectangle_outline(
            button_x, button_x + button_width,
            button_y, button_y + button_height,
            arcade.color.WHITE, 2
        )
        
        # 绘制按钮文字
        arcade.draw_text(
            "确定",
            button_x + button_width // 2,
            button_y + button_height // 2,
            arcade.color.WHITE,
            self.option_font_size,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
    
    def handle_option_click(self, x: float, y: float) -> Optional[NarrativeAction]:
        """
        处理选项点击
        
        Returns:
            被点击的动作，如果没有点击到选项则返回None
        """
        for button in self.option_buttons:
            if (button["left"] <= x <= button["right"] and
                button["bottom"] <= y <= button["top"]):
                return button["action"]
        return None
    
    def handle_confirm_click(self, x: float, y: float) -> bool:
        """
        处理确定按钮点击
        
        Returns:
            是否点击了确定按钮
        """
        if not self.confirm_button:
            return False
        
        return (self.confirm_button["left"] <= x <= self.confirm_button["right"] and
                self.confirm_button["bottom"] <= y <= self.confirm_button["top"])
    
    def is_visible(self) -> bool:
        """检查叙事场景是否可见"""
        return self.current_node is not None
    
    def hide(self):
        """隐藏叙事场景"""
        self.current_node = None
        self.selected_action = None
        self.current_result = None
        self.option_buttons.clear()
        self.confirm_button = None
        self.revealed_hidden_actions.clear()

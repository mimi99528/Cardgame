"""
战利品选择UI模块
战斗结束后显示掉落卡牌，玩家可三选一加入牌库
"""
import arcade
from typing import List, Optional, Callable
from models import Card
from ui_scale import S
from chinese_text_helper import prepare_text_for_arcade


class LootSelectionView(arcade.View):
    """战利品选择视图 - 让玩家从掉落的卡牌中选择一张加入牌库"""
    
    def __init__(self, cards: List[Card], on_selection_complete: Callable):
        """
        初始化战利品选择视图
        
        Args:
            cards: 可供选择的卡牌列表（建议3张，但支持1-5张）
            on_selection_complete: 回调函数，当选择完成时调用，参数为选中的卡牌或None
        """
        super().__init__()
        
        self.cards = cards[:5]  # 最多显示5张，但至少显示所有可用的
        self.on_selection_complete = on_selection_complete
        self.hovered_card_index = -1
        self.selected_card_index = -1
        self.selection_completed = False  # 防止重复完成
        
        # UI布局参数 - 放大卡牌尺寸
        self.card_width = S.px(280)  # 从200增加到280
        self.card_height = S.py(400)  # 从280增加到400
        self.card_spacing = S.px(50)  # 从40增加到50
        self.title_font_size = S.font(36)  # 从32增加到36
        self.instruction_font_size = S.font(20)  # 从18增加到20
        
    def on_draw(self):
        """绘制战利品选择界面"""
        self.clear()
        
        # 绘制背景
        arcade.set_background_color((20, 20, 30))
        
        # 绘制标题
        title_y = self.window.height - S.py(80)
        title_text = "选择一张卡牌加入牌库"
        
        processed_title = prepare_text_for_arcade(
            title_text,
            max_width=self.window.width - S.px(100),
            font_size=self.title_font_size
        )
        
        arcade.draw_text(
            processed_title,
            self.window.width / 2,
            title_y,
            arcade.color.GOLD,
            self.title_font_size,
            anchor_x="center",
            anchor_y="center",
            bold=True,
            multiline=True,
            width=int(self.window.width - S.px(100))
        )
        
        # 绘制说明文字
        instruction_y = title_y - S.py(70)
        card_count = len(self.cards)
        instruction_text = f"点击卡牌选择，或按ESC跳过（获得{card_count}张卡牌）"
        
        arcade.draw_text(
            instruction_text,
            self.window.width / 2,
            instruction_y,
            arcade.color.WHITE,
            self.instruction_font_size,
            anchor_x="center",
            anchor_y="center"
        )
        
        # 绘制卡牌
        self._draw_cards()
    
    def _draw_cards(self):
        """绘制可选的卡牌"""
        if not self.cards:
            return
        
        # 计算卡牌位置（居中排列）
        total_width = len(self.cards) * self.card_width + (len(self.cards) - 1) * self.card_spacing
        start_x = (self.window.width - total_width) / 2
        card_y = self.window.height / 2
        
        for i, card in enumerate(self.cards):
            card_x = start_x + i * (self.card_width + self.card_spacing) + self.card_width / 2
            
            # 检查是否悬停
            is_hovered = (i == self.hovered_card_index)
            is_selected = (i == self.selected_card_index)
            
            # 绘制卡牌背景和边框
            self._draw_card_frame(card_x, card_y, is_hovered, is_selected)
            
            # 绘制卡牌内容
            self._draw_card_content(card, card_x, card_y)
    
    def _draw_card_frame(self, x: float, y: float, is_hovered: bool, is_selected: bool):
        """绘制卡牌框架"""
        half_width = self.card_width / 2
        half_height = self.card_height / 2
        
        # 根据状态确定颜色
        if is_selected:
            bg_color = (50, 100, 50, 200)  # 绿色背景表示已选中
            border_color = arcade.color.GREEN
            border_width = 4
        elif is_hovered:
            bg_color = (80, 80, 100, 200)  # 高亮背景
            border_color = arcade.color.YELLOW
            border_width = 3
        else:
            bg_color = (40, 40, 50, 200)  # 普通背景
            border_color = arcade.color.WHITE
            border_width = 2
        
        # 绘制背景
        arcade.draw_lrbt_rectangle_filled(
            x - half_width, x + half_width,
            y - half_height, y + half_height,
            bg_color
        )
        
        # 绘制边框
        arcade.draw_lrbt_rectangle_outline(
            x - half_width, x + half_width,
            y - half_height, y + half_height,
            border_color,
            border_width
        )
        
        # 如果悬停，添加发光效果
        if is_hovered and not is_selected:
            glow_width = S.px(10)
            arcade.draw_lrbt_rectangle_outline(
                x - half_width - glow_width, x + half_width + glow_width,
                y - half_height - glow_width, y + half_height + glow_width,
                (255, 255, 200, 100),
                2
            )
    
    def _draw_card_content(self, card: Card, x: float, y: float):
        """绘制卡牌内容 - 复用手牌显示效果"""
        half_width = self.card_width / 2
        half_height = self.card_height / 2
        
        # 1. 卡牌图像（顶部）- 使用与手牌相同的渲染方式
        image_y = y + half_height - S.py(30)
        image_width = self.card_width * 0.75  # 卡图宽度为卡牌宽度的75%
        image_height = self.card_height * 0.35  # 卡图高度为卡牌高度的35%
        
        # 尝试加载卡图（复用ui_renderer的card_test_texture）
        try:
            from game_view import GameView
            # 获取全局窗口引用
            window = arcade.get_window()
            if hasattr(window, 'ui_renderer') and hasattr(window.ui_renderer, 'card_test_texture'):
                card_texture = window.ui_renderer.card_test_texture
                if card_texture:
                    arcade.draw_texture_rect(
                        card_texture,
                        arcade.XYWH(
                            x - image_width / 2,
                            image_y - image_height / 2,
                            image_width,
                            image_height
                        )
                    )
                else:
                    self._draw_card_placeholder(x, image_y, image_width, image_height)
            else:
                self._draw_card_placeholder(x, image_y, image_width, image_height)
        except:
            self._draw_card_placeholder(x, image_y, image_width, image_height)
        
        # 2. 卡牌名称（图像下方）
        name_y = image_y - S.py(90)
        
        # 自动计算字体大小以适应卡牌宽度
        max_name_width = int(self.card_width - S.px(40))
        name_font_size = S.font(22)  # 基础字体大小
        
        # 如果名称太长，缩小字体
        try:
            name_width = arcade.get_text_width(card.name, font_size=name_font_size)
            if name_width > max_name_width:
                name_font_size = int(name_font_size * max_name_width / name_width)
                # 确保字体不会太小
                name_font_size = max(S.font(16), name_font_size)
        except:
            pass  # 如果无法计算宽度，使用默认字体
        
        processed_name = prepare_text_for_arcade(
            card.name,
            max_width=max_name_width,
            font_size=name_font_size
        )
        
        arcade.draw_text(
            processed_name,
            x, name_y,
            arcade.color.GOLD,
            name_font_size,
            anchor_x="center",
            anchor_y="top",
            bold=True,
            multiline=True,
            width=max_name_width
        )
        
        # 3. 稀有度标识
        rarity_colors = {
            0: arcade.color.GRAY,      # 普通
            1: arcade.color.SKY_BLUE,  # 优秀
            2: arcade.color.INDIGO,    # 稀有
            3: arcade.color.GOLD       # 传说
        }
        rarity_color = rarity_colors.get(card.rarity.value, arcade.color.WHITE)
        
        rarity_names = ["普通", "优秀", "稀有", "传说"]
        rarity_name = rarity_names[card.rarity.value] if card.rarity.value < len(rarity_names) else "未知"
        
        rarity_y = name_y - S.py(40)
        arcade.draw_text(
            rarity_name,
            x, rarity_y,
            rarity_color,
            S.font(18),  # 从16增加到18
            anchor_x="center",
            anchor_y="top",
            bold=True
        )
        
        # 4. 卡牌描述（中部，增大的黑底区域）
        desc_start_y = rarity_y - S.py(30)
        desc_max_height = S.py(200)  # 从180增加到200
        
        # 绘制更大的描述背景
        desc_bg_padding = S.px(18)
        arcade.draw_lrbt_rectangle_filled(
            x - half_width + desc_bg_padding, 
            x + half_width - desc_bg_padding,
            desc_start_y - desc_max_height, 
            desc_start_y,
            (0, 0, 0, 200)  # 更深的黑色背景，透明度从180增加到200
        )
        
        # 处理并绘制描述文本 - 自动调整字体大小
        description = getattr(card, 'description', '') or getattr(card, 'desc', '') or "无描述"
        
        # 计算合适的字体大小
        desc_font_size = S.font(15)  # 基础字体大小从14增加到15
        max_desc_width = int(self.card_width - S.px(55))
        
        # 根据文本长度动态调整字体大小
        if len(description) > 120:  # 长文本
            desc_font_size = S.font(12)
        elif len(description) > 70:  # 中等文本
            desc_font_size = S.font(13)
        elif len(description) > 40:  # 较短文本
            desc_font_size = S.font(14)
        
        processed_desc = prepare_text_for_arcade(
            description,
            max_width=max_desc_width,
            font_size=desc_font_size
        )
        
        arcade.draw_text(
            processed_desc,
            x, desc_start_y - S.py(10),
            arcade.color.WHITE,
            desc_font_size,
            anchor_x="center",
            anchor_y="top",
            multiline=True,
            width=max_desc_width
        )
        
        # 5. 卡牌标签（底部）
        if hasattr(card, 'tags') and card.tags:
            tag_y = desc_start_y - desc_max_height - S.py(25)
            tag_texts = [tag.value for tag in card.tags[:4]]  # 最多显示4个标签
            tag_str = ", ".join(tag_texts)
            
            # 自动调整标签字体大小
            tag_font_size = S.font(13)  # 从12增加到13
            max_tag_width = int(self.card_width - S.px(35))
            
            if len(tag_str) > 50:
                tag_font_size = S.font(11)
            elif len(tag_str) > 30:
                tag_font_size = S.font(12)
            
            processed_tags = prepare_text_for_arcade(
                tag_str,
                max_width=max_tag_width,
                font_size=tag_font_size
            )
            
            arcade.draw_text(
                processed_tags,
                x, tag_y,
                arcade.color.LIGHT_BLUE,
                tag_font_size,
                anchor_x="center",
                anchor_y="top",
                multiline=True,
                width=max_tag_width
            )
    
    def _draw_card_placeholder(self, x: float, y: float, width: float, height: float):
        """绘制卡牌占位符（当没有卡图时）"""
        # 绘制深色背景
        arcade.draw_lrbt_rectangle_filled(
            x - width/2, x + width/2,
            y - height/2, y + height/2,
            (60, 60, 80, 200)
        )
        
        # 绘制边框
        arcade.draw_lrbt_rectangle_outline(
            x - width/2, x + width/2,
            y - height/2, y + height/2,
            arcade.color.WHITE,
            2
        )
        
        # 绘制问号
        arcade.draw_text(
            "?",
            x, y,
            arcade.color.GRAY,
            S.font(56),
            anchor_x="center",
            anchor_y="center"
        )
    
    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """鼠标移动事件"""
        if not self.cards:
            self.hovered_card_index = -1
            return
        
        # 计算卡牌位置
        total_width = len(self.cards) * self.card_width + (len(self.cards) - 1) * self.card_spacing
        start_x = (self.window.width - total_width) / 2
        card_y = self.window.height / 2
        
        # 检查鼠标是否在某个卡牌上
        self.hovered_card_index = -1
        for i in range(len(self.cards)):
            card_x = start_x + i * (self.card_width + self.card_spacing)
            
            if (card_x <= x <= card_x + self.card_width and
                card_y - self.card_height / 2 <= y <= card_y + self.card_height / 2):
                self.hovered_card_index = i
                break
    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """鼠标点击事件"""
        # 如果已经完成选择，忽略后续点击
        if self.selection_completed:
            print(f"[DEBUG] 已经完成选择，忽略点击")
            return
        
        if self.hovered_card_index >= 0:
            self.selected_card_index = self.hovered_card_index
            # 延迟一下再关闭，让玩家看到选中效果
            arcade.schedule(self._complete_selection, 0.3)
    
    def _complete_selection(self, delta_time):
        """完成选择"""
        # 防止重复执行
        if self.selection_completed:
            print(f"[DEBUG] _complete_selection 已经被调用过，跳过")
            return
        
        print(f"[DEBUG] LootSelectionView._complete_selection called")
        print(f"[DEBUG] selected_card_index: {self.selected_card_index}")
        print(f"[DEBUG] window._game_view: {self.window._game_view if hasattr(self.window, '_game_view') else None}")
        
        # 标记为已完成
        self.selection_completed = True
        
        if self.selected_card_index >= 0 and self.selected_card_index < len(self.cards):
            selected_card = self.cards[self.selected_card_index]
            self.on_selection_complete(selected_card)
        else:
            self.on_selection_complete(None)
        
        # 注意：不再自动返回GameView，让回调函数决定下一步显示什么视图
        # 如果回调函数需要返回GameView，它应该自己调用 show_view
        print(f"[DEBUG] LootSelectionView 完成选择，等待回调函数处理下一步")
    
    def on_key_press(self, key: int, modifiers: int):
        """键盘事件"""
        if key == arcade.key.ESCAPE:
            # 防止重复执行
            if self.selection_completed:
                print(f"[DEBUG] ESC 已经被处理过，跳过")
                return
            
            # ESC键跳过选择
            self.selection_completed = True
            self.on_selection_complete(None)
            
            # 注意：不再自动返回GameView，让回调函数决定下一步
            print(f"[DEBUG] LootSelectionView ESC跳过，等待回调函数处理下一步")

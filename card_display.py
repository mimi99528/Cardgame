"""
卡牌显示模块
负责卡牌的绘制和显示逻辑
"""
import arcade
from typing import Dict, Optional
from models import Card, Entity
from battle_system import BattleSystem
from config import CONSTANTS, CARD_TYPE_NAMES, RARITY_COLORS


class CardDisplay:
    """卡牌显示器 - 处理卡牌的绘制和交互"""
    
    def __init__(self, ui_renderer):
        """
        初始化卡牌显示器
        
        Args:
            ui_renderer: UIRenderer实例，用于文本绘制
        """
        self.ui_renderer = ui_renderer
        self.card_positions: Dict[Card, tuple] = {}
        self.hovered_card: Optional[Card] = None
    
    def draw_hand(self, battle: BattleSystem):
        """绘制手牌（根据当前行动的实体）"""
        current_entity = battle.current_entity
        if not current_entity:
            return
        
        # 如果是AI控制的实体，只显示手牌数量
        if current_entity.control_type.value == "ai":
            self._draw_ai_hand_count(current_entity)
            return
        
        hand = current_entity.hand
        if not hand:
            return
        
        # 计算卡牌位置
        card_width = CONSTANTS.CARD_WIDTH
        card_height = CONSTANTS.CARD_HEIGHT
        spacing = CONSTANTS.CARD_SPACING
        
        total_width = len(hand) * (card_width + spacing) - spacing
        start_x = (self.ui_renderer.window_width - total_width) / 2
        base_y = 60
        
        for i, card in enumerate(hand):
            x = start_x + i * (card_width + spacing) + card_width / 2
            y = base_y
            
            # 保存基础位置（不含悬停偏移）用于点击检测
            self.card_positions[card] = (x, y)
            
            # 如果卡牌被悬停，上移（仅用于绘制）
            draw_y = y
            if card == self.hovered_card:
                draw_y += CONSTANTS.CARD_HOVER_OFFSET
            
            # 绘制卡牌
            self._draw_card(card, x, draw_y, card_width, card_height)
    
    def _draw_card(self, card: Card, x, y, width, height):
        """绘制单张卡牌"""
        # 卡牌背景
        rarity_color = RARITY_COLORS.get(card.rarity, arcade.color.WHITE)
        arcade.draw_lrbt_rectangle_filled(
            x - width / 2, x + width / 2,
            y - height / 2, y + height / 2,
            rarity_color
        )
        
        # 卡牌边框
        rarity_colors_list = [arcade.color.BLACK, arcade.color.SKY_BLUE, 
                              arcade.color.INDIGO, arcade.color.GOLD]
        border_color = rarity_colors_list[card.rarity.value] if hasattr(card.rarity, 'value') else arcade.color.BLACK
        arcade.draw_lrbt_rectangle_outline(
            x - width / 2, x + width / 2,
            y - height / 2, y + height / 2,
            border_color, 10
        )
        
        # 卡牌名称背景
        name_bg_y_bottom = y - height / 2 + 110
        name_bg_y_top = y - height / 2 + 150
        arcade.draw_lrbt_rectangle_filled(
            x - 100, x + 100,
            name_bg_y_bottom, name_bg_y_top,
            arcade.color.DARK_GRAY
        )
        arcade.draw_lrbt_rectangle_outline(
            x - 100, x + 100,
            name_bg_y_bottom, name_bg_y_top,
            arcade.color.WHITE, 5
        )
        
        # 卡牌名称
        self.ui_renderer.draw_text(
            card.name,
            x, name_bg_y_bottom + 20,
            arcade.color.WHITE,
            self.ui_renderer.title_font_size,
            anchor_x="center", anchor_y="center", bold=True
        )
        
        # 卡牌类型背景
        type_bg_y_bottom = y - height / 2 + 75
        type_bg_y_top = y - height / 2 + 105
        arcade.draw_lrbt_rectangle_filled(
            x - 50, x + 50,
            type_bg_y_bottom, type_bg_y_top,
            arcade.color.DARK_GRAY
        )
        
        # 卡牌类型
        type_name = CARD_TYPE_NAMES.get(card.card_type, "未知")
        self.ui_renderer.draw_text(
            type_name,
            x, type_bg_y_bottom + 15,
            arcade.color.WHITE,
            self.ui_renderer.title_font_size,
            anchor_x="center", anchor_y="center"
        )
        
        # AP消耗
        self._draw_ap_cost(card, x, y, width, height)
        
        # 效果值显示
        self._draw_effect_values(card, x, y, width, height)
        
        # 如果是悬停状态，显示描述
        if card == self.hovered_card:
            self._draw_card_description(card, x, y, width, height)
    
    def _draw_ap_cost(self, card: Card, x, y, width, height):
        """绘制AP消耗"""
        ap_x = x + width / 2 - 15
        ap_y = y + height / 2 - 15
        
        texture = self.ui_renderer.ap_32_texture if hasattr(self.ui_renderer, 'ap_32_texture') else None
        
        for i in range(card.ap_cost):
            if texture:
                arcade.draw_texture_rect(
                    texture,
                    arcade.XYWH(ap_x - 10, ap_y - i * 25 - 10, 20, 20)
                )
            else:
                arcade.draw_circle_filled(ap_x, ap_y - i * 25, 8, arcade.color.BLUE)
                arcade.draw_circle_outline(ap_x, ap_y - i * 25, 8, arcade.color.WHITE, 2)
    
    def _draw_effect_values(self, card: Card, x, y, width, height):
        """绘制效果值（HP、格挡等）"""
        if "hp" in card.effects:
            value = abs(card.effects["hp"])
            icon_x = x - width / 2 + 30
            icon_y = y + height / 2 - 30
            
            # 白色背景框
            arcade.draw_lrbt_rectangle_filled(
                icon_x - 27, icon_x + 27,
                icon_y - 15, icon_y + 15,
                arcade.color.WHITE
            )
            arcade.draw_lrbt_rectangle_outline(
                icon_x - 27, icon_x + 27,
                icon_y - 15, icon_y + 15,
                arcade.color.BLACK, 2
            )
            
            # 图标
            phy_texture = self.ui_renderer.phy_texture if hasattr(self.ui_renderer, 'phy_texture') else None
            def_texture = self.ui_renderer.def_texture if hasattr(self.ui_renderer, 'def_texture') else None
            
            if "phy" in card.card_type.value and phy_texture:
                arcade.draw_texture_rect(
                    phy_texture,
                    arcade.XYWH(icon_x - 20, icon_y - 10, 20, 20)
                )
            elif def_texture:
                arcade.draw_texture_rect(
                    def_texture,
                    arcade.XYWH(icon_x - 20, icon_y - 10, 20, 20)
                )
            
            # 数值
            self.ui_renderer.draw_text(
                str(value),
                icon_x + 10, icon_y,
                arcade.color.BLACK,
                self.ui_renderer.number_font_size,
                anchor_x="center", anchor_y="center", bold=True
            )
        
        if "block" in card.effects:
            value = card.effects["block"]
            icon_x = x - width / 2 + 30
            icon_y = y + height / 2 - 30
            
            # 白色背景框
            arcade.draw_lrbt_rectangle_filled(
                icon_x - 27, icon_x + 27,
                icon_y - 15, icon_y + 15,
                arcade.color.WHITE
            )
            arcade.draw_lrbt_rectangle_outline(
                icon_x - 27, icon_x + 27,
                icon_y - 15, icon_y + 15,
                arcade.color.BLACK, 2
            )
            
            # 图标
            def_texture = self.ui_renderer.def_texture if hasattr(self.ui_renderer, 'def_texture') else None
            if def_texture:
                arcade.draw_texture_rect(
                    def_texture,
                    arcade.XYWH(icon_x - 20, icon_y - 10, 20, 20)
                )
            
            # 数值
            self.ui_renderer.draw_text(
                str(value),
                icon_x + 10, icon_y,
                arcade.color.BLACK,
                self.ui_renderer.number_font_size,
                anchor_x="center", anchor_y="center", bold=True
            )
    
    def _draw_card_description(self, card: Card, x, y, width, height):
        """绘制卡牌描述"""
        overlay_color = (64, 64, 64, 200)
        desc_y_start = y - height / 2 + 41
        desc_y_end = y + height / 2 - 46
        
        arcade.draw_lrbt_rectangle_filled(
            x - (width - 10) / 2, x + (width - 10) / 2,
            desc_y_start, desc_y_end,
            overlay_color
        )
        
        self.ui_renderer.draw_text(
            card.description,
            x, y - 18,
            arcade.color.WHITE,
            self.ui_renderer.text_font_size,
            anchor_x="center", anchor_y="center",
            multiline=True, width=width - 30
        )
    
    def _draw_ai_hand_count(self, entity: Entity):
        """绘制AI手牌数量（用黑框表示）"""
        hand_size = len(entity.hand)
        if hand_size == 0:
            return
        
        box_width = 80
        box_height = 100
        spacing = 15
        
        total_width = hand_size * (box_width + spacing) - spacing
        start_x = (self.ui_renderer.window_width - total_width) / 2
        base_y = 60
        
        for i in range(hand_size):
            x = start_x + i * (box_width + spacing) + box_width / 2
            y = base_y
            
            # 绘制黑色背景
            arcade.draw_lrbt_rectangle_filled(
                x - box_width / 2, x + box_width / 2,
                y - box_height / 2, y + box_height / 2,
                arcade.color.BLACK
            )
            
            # 绘制边框
            arcade.draw_lrbt_rectangle_outline(
                x - box_width / 2, x + box_width / 2,
                y - box_height / 2, y + box_height / 2,
                arcade.color.GRAY, 3
            )
        
        # 显示手牌数量
        self.ui_renderer.draw_text(
            f"手牌: {hand_size}",
            self.ui_renderer.window_width / 2,
            base_y + box_height / 2 + 20,
            arcade.color.WHITE,
            self.ui_renderer.title_font_size,
            anchor_x="center", anchor_y="center", bold=True
        )
    
    def check_hover(self, x: float, y: float):
        """检查鼠标是否悬停在卡牌上"""
        old_hovered = self.hovered_card
        self.hovered_card = None
        
        for card, (card_x, card_y) in list(self.card_positions.items()):
            half_width = CONSTANTS.CARD_WIDTH / 2
            half_height = CONSTANTS.CARD_HEIGHT / 2
            
            # 考虑悬停偏移
            check_y = card_y
            if card == old_hovered:
                check_y += CONSTANTS.CARD_HOVER_OFFSET
            
            if (card_x - half_width <= x <= card_x + half_width and
                check_y - half_height <= y <= check_y + half_height):
                self.hovered_card = card
                break
        
        return self.hovered_card
    
    def check_click(self, x: float, y: float) -> Optional[Card]:
        """检查是否点击了卡牌"""
        for card, (card_x, card_y) in self.card_positions.items():
            half_width = CONSTANTS.CARD_WIDTH / 2
            half_height = CONSTANTS.CARD_HEIGHT / 2
            
            # 考虑悬停偏移
            check_y = card_y
            if card == self.hovered_card:
                check_y += CONSTANTS.CARD_HOVER_OFFSET
            
            if (card_x - half_width <= x <= card_x + half_width and
                check_y - half_height <= y <= check_y + half_height):
                return card
        
        return None
    
    def clear_positions(self):
        """清空卡牌位置缓存"""
        self.card_positions.clear()

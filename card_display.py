"""
卡牌显示模块
负责卡牌的绘制和显示逻辑
"""
import arcade
import time
from typing import Dict, Optional, List
from models import Card, Entity
from battle_system import BattleSystem
from config import CONSTANTS, CARD_TYPE_NAMES, RARITY_COLORS


class CardDisplay:
    """卡牌显示器 - 处理卡牌的绘制和交互"""
    
    def __init__(self, ui_renderer):
        """
        初始化卡牌显示器
            
        Args:
            ui_renderer: UIRenderer实例,用于文本绘制
        """
        self.ui_renderer = ui_renderer
        self.current_battle: Optional[BattleSystem] = None  # 保存当前战斗引用
        self.card_positions: Dict[int, tuple] = {}  # 使用id(card)作为键
        self.hovered_card: Optional[Card] = None
        self.dragged_card: Optional[Card] = None  # 正在拖动的卡牌
        self.drag_start_pos: Optional[tuple] = None  # 拖动起始位置
        self.drag_current_pos: Optional[tuple] = None  # 拖动当前位置(鼠标位置)
            
        # 动画相关
        self.rising_cards: Dict[int, dict] = {}  # 正在上升的卡牌 {id(card): {'start_time': float, 'duration': float}}
            
        # 卡牌显示位置控制(统一管理卡牌的位置和动画)
        self.card_display_posis: Dict[int, dict] = {}  # {id(card): {'target_y': float, 'current_y': float, 'animating': bool, 'anim_start_time': float, 'anim_duration': float}}
    
    def draw_hand(self, battle: BattleSystem):
        """绘制手牌（根据当前行动的实体）"""
        # 保存当前battle引用，供其他方法使用
        self.current_battle = battle
        
        current_entity = battle.current_entity
        if not current_entity:
            return
        
        # 更新动画状态
        self.update_animations()
        
        # 清理不在手牌中的卡牌位置数据
        self.cleanup_card_positions(current_entity.hand)
        
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
            # 跳过正在拖动的卡牌(不绘制在手牌中)
            if card == self.dragged_card:
                continue
                    
            x = start_x + i * (card_width + spacing) + card_width / 2
            base_y = 60
                    
            # 使用卡牌的唯一ID作为键
            card_id = id(card)
                    
            # 初始化或更新卡牌显示位置
            if card_id not in self.card_display_posis:
                # 新卡牌,设置初始位置为目标位置
                self.card_display_posis[card_id] = {
                    'target_y': base_y,
                    'current_y': base_y,
                    'animating': False,
                    'anim_start_time': 0,
                    'anim_duration': 0,
                    'card_ref': card  # 保存卡牌引用
                }
            else:
                # 更新目标位置
                self.card_display_posis[card_id]['target_y'] = base_y
                # 确保卡牌引用正确
                self.card_display_posis[card_id]['card_ref'] = card
                    
            # 更新动画状态
            self._update_card_animation(card_id)
                    
            # 使用当前动画位置
            y = self.card_display_posis[card_id]['current_y']
            # print(card, y)
                    
            # 保存基础位置(不含悬停偏移)用于点击检测
            self.card_positions[card_id] = (x, y)
                    
            # 如果卡牌被悬停,上移(仅用于绘制)
            draw_y = y
            if id(card) == id(self.hovered_card):
                draw_y += CONSTANTS.CARD_HOVER_OFFSET
                    
            # 绘制卡牌
            self._draw_card(card, x, draw_y, card_width, card_height)
        
        # 绘制拖动中的卡牌（跟随鼠标）
        if self.dragged_card and self.drag_current_pos:
            self._draw_dragged_card(self.dragged_card, self.drag_current_pos[0], self.drag_current_pos[1])
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
        
        # 卡牌图片（使用card_test.png）
        card_test_texture = self.ui_renderer.card_test_texture if hasattr(self.ui_renderer, 'card_test_texture') else None
        if card_test_texture:
            # 在卡牌中央绘制卡图，留出边距
            image_width = width * 0.7
            image_height = height * 0.45
            arcade.draw_texture_rect(
                card_test_texture,
                arcade.XYWH(
                    x - image_width / 2,
                    y + 10 - image_height / 2,
                    image_width,
                    image_height
                )
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
        if id(card) == id(self.hovered_card):
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
        """绘制卡牌描述（悬停时显示）"""
        description_y = y + height / 2 + 10
        
        # 计算预期效果值（使用保存的battle引用）
        expected = self._calculate_expected_values(card, self.current_battle)
        
        # 如果有结构化效果列表，使用多行显示
        if isinstance(card.effects, list):
            # 构建描述文本
            desc_lines = []
            for effect in card.effects:
                effect_type = effect.get("type", "")
                if effect_type == "emy_dmg":
                    dice_expr = effect.get("dice", "")
                    if dice_expr:
                        desc_lines.append(f"对敌人造成{dice_expr}点物理伤害")
                elif effect_type == "self_heal":
                    amount = effect.get("amount", 0)
                    desc_lines.append(f"恢复{amount}点生命值")
                elif effect_type == "self_block":
                    dice_expr = effect.get("dice", "")
                    if dice_expr:
                        desc_lines.append(f"获得{dice_expr}点格挡")
                    else:
                        amount = effect.get("amount", 0)
                        desc_lines.append(f"获得{amount}点格挡")
                elif effect_type == "apply_buff":
                    buff_name = effect.get("buff_name", "")
                    duration = effect.get("duration", 0)
                    desc_lines.append(f"施加{buff_name}({duration}回合)")
            
            # 添加预期效果值
            if expected:
                desc_lines.extend(expected)
            
            # 绘制多行描述
            line_height = 20
            total_height = len(desc_lines) * line_height
            
            # 背景框
            arcade.draw_lrbt_rectangle_filled(
                x - width / 2 - 5, x + width / 2 + 5,
                description_y, description_y + total_height + 10,
                (0, 0, 0, 200)
            )
            
            # 绘制每一行
            for i, line in enumerate(desc_lines):
                line_y = description_y + total_height - i * line_height - 10
                self.ui_renderer.draw_text(
                    line,
                    x, line_y,
                    arcade.color.WHITE,
                    self.ui_renderer.text_font_size - 2,
                    anchor_x="center", anchor_y="center"
                )
        else:
            # 旧版字典格式，单行显示
            description = card.description if hasattr(card, 'description') and card.description else "无描述"
            
            # 添加预期效果值
            if expected:
                expected_str = ", ".join(expected)
                description += f"\n[{expected_str}]"
            
            # 简单绘制（可能需要改进为多行）
            self.ui_renderer.draw_text(
                description,
                x, description_y + 50,
                arcade.color.WHITE,
                self.ui_renderer.text_font_size,
                anchor_x="center", anchor_y="top"
            )
    
    def _calculate_expected_values(self, card: Card, battle: BattleSystem = None) -> list:
        """
        计算卡牌的预期效果数值
        
        Args:
            card: 卡牌对象
            battle: 战斗系统对象（可选，用于获取当前实体）
        
        Returns:
            描述列表，如 ["伤害: 15-20", "格挡: 10"]
        """
        expected = []
        
        # 获取当前实体（用于计算属性加值）
        current_entity = None
        if battle:
            current_entity = battle.current_entity
        elif hasattr(self.ui_renderer, 'battle') and self.ui_renderer.battle:
            current_entity = self.ui_renderer.battle.current_entity
        
        # 计算属性加值（如果有实体且卡牌有stat_ratios）
        stat_bonus = 0
        if current_entity and hasattr(current_entity, 'stats') and card.stat_ratios:
            try:
                stat_bonus = card.get_stat_bonus(current_entity.stats)
            except Exception as e:
                # 如果计算失败，记录错误但不中断程序
                print(f"警告: 计算属性加值失败 - {e}")
                stat_bonus = 0
        
        # 处理结构化效果列表
        if isinstance(card.effects, list):
            for effect in card.effects:
                effect_type = effect.get("type", "")
                
                # 伤害效果
                if effect_type == "emy_dmg":
                    dice_expr = effect.get("dice", "")
                    if dice_expr:
                        # 解析骰子表达式
                        try:
                            parts = dice_expr.lower().split('d')
                            if len(parts) == 2:
                                num_dice = int(parts[0])
                                sides = int(parts[1])
                                min_damage = num_dice * 1
                                max_damage = num_dice * sides
                                # 添加属性加值到显示
                                if stat_bonus != 0:
                                    expected.append(f"伤害: {min_damage+stat_bonus}-{max_damage+stat_bonus} ({dice_expr}{stat_bonus:+d})")
                                else:
                                    expected.append(f"伤害: {min_damage}-{max_damage} ({dice_expr})")
                        except:
                            pass
                
                # 治疗效果
                elif effect_type == "self_heal":
                    amount = effect.get("amount", 0)
                    # 添加属性加值到显示
                    if stat_bonus != 0:
                        expected.append(f"治疗: {amount+stat_bonus} (基础{amount}{stat_bonus:+d})")
                    else:
                        expected.append(f"治疗: {amount}")
                
                # 格挡效果
                elif effect_type == "self_block":
                    dice_expr = effect.get("dice", "")
                    if dice_expr:
                        try:
                            parts = dice_expr.lower().split('d')
                            if len(parts) == 2:
                                num_dice = int(parts[0])
                                sides = int(parts[1])
                                min_block = num_dice * 1
                                max_block = num_dice * sides
                                # 添加属性加值到显示
                                if stat_bonus != 0:
                                    expected.append(f"格挡: {min_block+stat_bonus}-{max_block+stat_bonus} ({dice_expr}{stat_bonus:+d})")
                                else:
                                    expected.append(f"格挡: {min_block}-{max_block} ({dice_expr})")
                        except:
                            pass
                    else:
                        amount = effect.get("amount", 0)
                        # 添加属性加值到显示
                        if stat_bonus != 0:
                            expected.append(f"格挡: {amount+stat_bonus} (基础{amount}{stat_bonus:+d})")
                        else:
                            expected.append(f"格挡: {amount}")
        
        # 兼容旧版字典格式
        elif isinstance(card.effects, dict):
            if "hp" in card.effects:
                damage = abs(card.effects["hp"])
                expected.append(f"伤害: {damage}")
            
            if "hp_dice" in card.effects:
                # 新版骰子表达式
                dice_expr = card.effects["hp_dice"]
                try:
                    parts = dice_expr.lower().split('d')
                    if len(parts) == 2:
                        num_dice = int(parts[0])
                        sides = int(parts[1])
                        min_damage = num_dice * 1
                        max_damage = num_dice * sides
                        expected.append(f"伤害: {min_damage}-{max_damage} ({dice_expr})")
                except:
                    pass
            
            if "block" in card.effects:
                block = card.effects["block"]
                expected.append(f"格挡: {block}")
            
            if "block_dice" in card.effects:
                # 新版骰子表达式
                dice_expr = card.effects["block_dice"]
                try:
                    parts = dice_expr.lower().split('d')
                    if len(parts) == 2:
                        num_dice = int(parts[0])
                        sides = int(parts[1])
                        min_block = num_dice * 1
                        max_block = num_dice * sides
                        expected.append(f"格挡: {min_block}-{max_block} ({dice_expr})")
                except:
                    pass
        
        return expected
    
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
        
        for card_id, (card_x, card_y) in list(self.card_positions.items()):
            # 从card_display_posis获取卡牌引用
            if card_id not in self.card_display_posis:
                continue
            card = self.card_display_posis[card_id].get('card_ref')
            if card is None:
                continue
            
            half_width = CONSTANTS.CARD_WIDTH / 2
            half_height = CONSTANTS.CARD_HEIGHT / 2
            
            # 考虑悬停偏移
            check_y = card_y
            if id(card) == id(old_hovered):
                check_y += CONSTANTS.CARD_HOVER_OFFSET
            
            if (card_x - half_width <= x <= card_x + half_width and
                check_y - half_height <= y <= check_y + half_height):
                self.hovered_card = card
                break
        
        return self.hovered_card
    
    def check_click(self, x: float, y: float) -> Optional[Card]:
        """检查是否点击了卡牌"""
        for card_id, (card_x, card_y) in self.card_positions.items():
            # 从card_display_posis获取卡牌引用
            if card_id not in self.card_display_posis:
                continue
            card = self.card_display_posis[card_id].get('card_ref')
            if card is None:
                continue
            
            half_width = CONSTANTS.CARD_WIDTH / 2
            half_height = CONSTANTS.CARD_HEIGHT / 2
            
            # 考虑悬停偏移
            check_y = card_y
            if id(card) == id(self.hovered_card):
                check_y += CONSTANTS.CARD_HOVER_OFFSET
            
            if (card_x - half_width <= x <= card_x + half_width and
                check_y - half_height <= y <= check_y + half_height):
                return card
        
        return None
    
    def start_drag(self, x: float, y: float) -> Optional[Card]:
        """开始拖动卡牌"""
        card = self.check_click(x, y)
        if card:
            self.dragged_card = card
            self.drag_start_pos = (x, y)
            self.drag_current_pos = (x, y)  # 关键修复：立即设置当前位置
        return card
    
    def update_drag(self, x: float, y: float):
        """更新拖动位置"""
        if self.dragged_card:
            self.drag_current_pos = (x, y)
    
    def end_drag(self, x: float, y: float) -> Optional[Card]:
        """结束拖动，返回拖动的卡牌（如果有）"""
        card = self.dragged_card
        self.dragged_card = None
        self.drag_start_pos = None
        self.drag_current_pos = None  # 清除拖动位置
        return card
    
    def is_dragging(self) -> bool:
        """检查是否正在拖动"""
        return self.dragged_card is not None
    
    def clear_drag(self):
        """清除拖动状态"""
        self.dragged_card = None
        self.drag_start_pos = None
        self.drag_current_pos = None  # 清除拖动位置
    
    def _update_card_animation(self, card_id: int):
        """
        更新单个卡牌的动画状态
            
        Args:
            card_id: 卡牌的唯一ID
        """
        if card_id not in self.card_display_posis:
            return
            
        pos_data = self.card_display_posis[card_id]
            
        if not pos_data['animating']:
            # 没有动画,直接设置为目标位置
            pos_data['current_y'] = pos_data['target_y']
            return
            
        # 计算动画进度
        current_time = time.time()
        elapsed = current_time - pos_data['anim_start_time']
            
        if elapsed >= pos_data['anim_duration']:
            # 动画完成
            pos_data['current_y'] = pos_data['target_y']
            pos_data['animating'] = False
            return
            
        # 计算进度 (0.0 - 1.0)
        progress = elapsed / pos_data['anim_duration']
            
        # 使用缓动函数(ease-out)
        ease_progress = 1 - (1 - progress) ** 3  # cubic ease-out
            
        # 插值计算当前位置
        pos_data['current_y'] = (
            pos_data['target_y'] + 
            (pos_data.get('start_y', pos_data['target_y']) - pos_data['target_y']) * (1 - ease_progress)
        )
    
    def start_rising_animation(self, card: Card, duration: float = 0.5):
        """
        启动卡牌上升动画
            
        Args:
            card: 要播放动画的卡牌
            duration: 动画持续时间(秒)
        """
        # 计算起始位置(从屏幕下方)
        start_y_position = -CONSTANTS.WINDOW_HEIGHT * 0.5
            
        # 使用卡牌的唯一ID
        card_id = id(card)
            
        # 获取或创建卡牌位置数据
        if card_id not in self.card_display_posis:
            self.card_display_posis[card_id] = {
                'target_y': 60,  # 默认目标位置
                'current_y': start_y_position,  # 从屏幕下方开始
                'animating': True,
                'anim_start_time': time.time(),
                'anim_duration': duration,
                'start_y': start_y_position,
                'card_ref': card  # 保存卡牌引用
            }
        else:
            # 设置动画参数
            pos_data = self.card_display_posis[card_id]
            # 关键修复:无论卡牌当前在哪里,都从屏幕下方开始动画
            pos_data['start_y'] = start_y_position
            pos_data['current_y'] = start_y_position  # 重置当前位置到下方
            pos_data['target_y'] = 60  # 确保目标位置正确
            pos_data['animating'] = True
            pos_data['anim_start_time'] = time.time()
            pos_data['anim_duration'] = duration
            pos_data['card_ref'] = card  # 更新卡牌引用
    
    def update_animations(self):
        """更新所有动画状态"""
        # 清理已完成的动画
        cards_to_clean = []
        for card_id, pos_data in self.card_display_posis.items():
            if pos_data['animating']:
                current_time = time.time()
                elapsed = current_time - pos_data['anim_start_time']
                if elapsed >= pos_data['anim_duration']:
                    pos_data['current_y'] = pos_data['target_y']
                    pos_data['animating'] = False
                    cards_to_clean.append(card_id)
            
        # 移除不在手牌中的卡牌位置数据
        # (这个需要在外部调用,传入当前手牌列表)
    
    def cleanup_card_positions(self, current_hand: List[Card]):
        """
        清理不在当前手牌中的卡牌位置数据
        
        Args:
            current_hand: 当前手牌列表
        """
        # 获取当前手牌中所有卡牌的ID
        current_hand_ids = set(id(card) for card in current_hand)
        
        # 清理不在当前手牌中的卡牌
        cards_to_remove = [card_id for card_id in self.card_display_posis if card_id not in current_hand_ids]
        for card_id in cards_to_remove:
            del self.card_display_posis[card_id]
    
    def clear_positions(self):
        """清空卡牌位置缓存"""
        self.card_positions.clear()
    
    def clear_all_card_references(self):
        """
        彻底清除所有卡牌相关的引用和状态
        在回合切换时调用，确保旧卡牌对象被完全清理
        """
        # 清除所有卡牌位置缓存
        self.card_positions.clear()
        
        # 清除所有卡牌显示位置和动画状态
        self.card_display_posis.clear()
        
        # 清除悬停状态
        self.hovered_card = None
        
        # 清除拖动状态
        self.dragged_card = None
        self.drag_start_pos = None
        self.drag_current_pos = None
        
        # 清除上升动画状态
        self.rising_cards.clear()
        
        # 强制垃圾回收（可选）
        import gc
        gc.collect()
    
    def _draw_dragged_card(self, card: Card, x: float, y: float):
        """
        绘制拖动中的卡牌（跟随鼠标的小卡牌）
        
        Args:
            card: 正在拖动的卡牌
            x, y: 鼠标当前位置
        """
        # 缩小版的卡牌尺寸
        drag_width = CONSTANTS.CARD_WIDTH * 0.6  # 60% 大小
        drag_height = CONSTANTS.CARD_HEIGHT * 0.6
        
        # 卡牌背景（使用稀有度颜色）
        rarity_color = RARITY_COLORS.get(card.rarity, arcade.color.WHITE)
        arcade.draw_lrbt_rectangle_filled(
            x - drag_width / 2, x + drag_width / 2,
            y - drag_height / 2, y + drag_height / 2,
            rarity_color
        )
        
        # 卡牌边框
        rarity_colors_list = [arcade.color.BLACK, arcade.color.SKY_BLUE, 
                              arcade.color.INDIGO, arcade.color.GOLD]
        border_color = rarity_colors_list[card.rarity.value] if hasattr(card.rarity, 'value') else arcade.color.BLACK
        arcade.draw_lrbt_rectangle_outline(
            x - drag_width / 2, x + drag_width / 2,
            y - drag_height / 2, y + drag_height / 2,
            border_color, 8
        )
        
        # 半透明遮罩效果（表示正在拖动）
        overlay_color = (255, 255, 255, 100)
        arcade.draw_lrbt_rectangle_filled(
            x - drag_width / 2, x + drag_width / 2,
            y - drag_height / 2, y + drag_height / 2,
            overlay_color
        )
        
        # 卡牌名称（简化版）
        self.ui_renderer.draw_text(
            card.name,
            x, y,
            arcade.color.WHITE,
            int(self.ui_renderer.title_font_size * 0.8),
            anchor_x="center", anchor_y="center", bold=True
        )
        
        # AP消耗指示器（右上角）
        ap_x = x + drag_width / 2 - 10
        ap_y = y + drag_height / 2 - 10
        
        texture = self.ui_renderer.ap_32_texture if hasattr(self.ui_renderer, 'ap_32_texture') else None
        
        if texture:
            arcade.draw_texture_rect(
                texture,
                arcade.XYWH(ap_x - 8, ap_y - 8, 16, 16)
            )
        else:
            arcade.draw_circle_filled(ap_x, ap_y, 6, arcade.color.BLUE)
            arcade.draw_circle_outline(ap_x, ap_y, 6, arcade.color.WHITE, 2)
        
        self.ui_renderer.draw_text(
            str(card.ap_cost),
            ap_x, ap_y,
            arcade.color.WHITE,
            int(self.ui_renderer.number_font_size * 0.7),
            anchor_x="center", anchor_y="center", bold=True
        )

"""
卡组编辑系统模块
允许玩家在战斗后编辑卡组，增删改卡牌
"""
import arcade
from typing import List, Optional, Callable, Dict
from models import Card, Entity
from config import Rarity, RARITY_COLORS, CONSTANTS
from ui_scale import S
from chinese_text_helper import prepare_text_for_arcade


class DeckEditView(arcade.View):
    """卡组编辑视图 - 让玩家编辑自己的卡组"""
    
    def __init__(self, player: Entity, on_edit_complete: Callable):
        """
        初始化卡组编辑视图
        
        Args:
            player: 玩家实体
            on_edit_complete: 回调函数，当编辑完成时调用
        """
        super().__init__()
        
        self.player = player
        self.on_edit_complete = on_edit_complete
        
        # UI状态
        self.hovered_card_index = -1  # 牌库中悬停的卡牌索引
        self.hovered_deck_card_index = -1  # 卡组中悬停的卡牌索引
        self.selected_card_index = -1  # 选中的卡牌索引（用于删除）
        self.selection_completed = False
        
        # Sprite列表用于碰撞检测
        self.library_card_sprites = arcade.SpriteList()  # 牌库卡牌Sprite
        self.deck_card_sprites = arcade.SpriteList()     # 卡组卡牌Sprite
        self.card_sprite_map = {}  # Sprite到卡牌索引的映射
        
        # 布局参数
        self.card_width = S.px(200)
        self.card_height = S.py(280)
        self.deck_card_width = S.px(400)  # 卡组中的卡牌显示为长条
        self.deck_card_height = S.py(60)
        self.card_spacing = S.px(30)
        self.title_font_size = S.font(32)
        self.instruction_font_size = S.font(18)
        
        # 左右面板位置
        self.left_panel_x = S.px(100)  # 牌库区域左侧
        self.right_panel_x = self.window.width - S.px(500)  # 卡组区域左侧
        
        # 滚动偏移（如果卡牌太多）
        self.library_scroll_offset = 0  # 牌库滚动偏移
        self.deck_scroll_offset = 0  # 卡组滚动偏移
        self.max_library_visible_rows = 3  # 牌库最多显示3行
        
        # 滚动条参数
        self.scrollbar_width = S.px(16)
        self.scrollbar_color = arcade.color.LIGHT_GRAY
        self.scrollbar_handle_color = arcade.color.SILVER
        
        # 同名卡牌计数（用于验证限制）
        self._update_deck_card_counts()
        
        # 悬停卡牌的详细信息（用于tooltip）
        self.tooltip_card = None
        self.tooltip_x = 0
        self.tooltip_y = 0
    
    def _update_deck_card_counts(self):
        """更新卡组中同名卡牌的计数"""
        self.deck_card_counts: Dict[str, int] = {}
        for card in self.player.deck:
            name = card.name
            if name not in self.deck_card_counts:
                self.deck_card_counts[name] = 0
            self.deck_card_counts[name] += 1
    
    def _update_card_sprites(self):
        """更新卡牌Sprite列表（用于碰撞检测）"""
        # 清空现有Sprite
        self.library_card_sprites.clear()
        self.deck_card_sprites.clear()
        self.card_sprite_map.clear()
        
        # 创建牌库卡牌Sprite
        all_cards = self._get_all_available_cards()
        cards_per_row = 4
        max_visible_cards = self.max_library_visible_rows * cards_per_row
        visible_start = self.library_scroll_offset * cards_per_row
        visible_end = min(len(all_cards), visible_start + max_visible_cards)
        visible_cards = all_cards[visible_start:visible_end]
        
        library_title_y = self.window.height - S.py(120)
        start_x = self.left_panel_x + S.px(20)
        start_y = library_title_y - S.py(150)
        row_spacing = self.card_height + S.py(20)
        col_spacing = self.card_width + self.card_spacing
        
        for i, card in enumerate(visible_cards):
            row = i // cards_per_row
            col = i % cards_per_row
            
            card_x = start_x + col * col_spacing + self.card_width / 2
            card_y = start_y - row * row_spacing
            
            # 创建一个不可见的Sprite用于碰撞检测
            sprite = arcade.SpriteSolidColor(int(self.card_width), int(self.card_height), (0, 0, 0, 0))
            sprite.center_x = card_x
            sprite.center_y = card_y
            self.library_card_sprites.append(sprite)
            
            # 映射Sprite索引到卡牌全局索引
            global_index = visible_start + i
            self.card_sprite_map[f"library_{len(self.library_card_sprites) - 1}"] = ('library', global_index)
        
        # 创建卡组卡牌Sprite
        deck_title_y = self.window.height - S.py(120)
        deck_start_y = deck_title_y - S.py(70)
        card_spacing_y = self.deck_card_height + S.py(10)
        
        visible_start = max(0, self.deck_scroll_offset)
        visible_end = min(len(self.player.deck), visible_start + 12)
        
        for i in range(visible_start, visible_end):
            card_y = deck_start_y - (i - visible_start) * card_spacing_y
            
            # 创建一个不可见的Sprite用于碰撞检测
            sprite = arcade.SpriteSolidColor(int(self.deck_card_width), int(self.deck_card_height), (0, 0, 0, 0))
            # 修复：Sprite中心点应该与绘制的中心点一致
            # 绘制时 x 是左边界，但 draw_lrbt_rectangle 使用 x-half_width 到 x+half_width
            # 所以实际中心点是 x（即 right_panel_x + 20）
            sprite.center_x = self.right_panel_x + S.px(20)
            sprite.center_y = card_y
            self.deck_card_sprites.append(sprite)
            
            # 映射Sprite索引到卡牌索引
            self.card_sprite_map[f"deck_{len(self.deck_card_sprites) - 1}"] = ('deck', i)
    
    def on_draw(self):
        """绘制卡组编辑界面"""
        self.clear()
        
        # 绘制背景
        arcade.set_background_color((25, 25, 35))
        
        # 绘制标题
        title_y = self.window.height - S.py(60)
        title_text = "卡组编辑"
        
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
        instruction_y = title_y - S.py(50)
        instruction_text = "点击牌库中的卡牌添加到卡组 | 点击卡组中的卡牌删除 | ESC退出"
        
        arcade.draw_text(
            instruction_text,
            self.window.width / 2,
            instruction_y,
            arcade.color.WHITE,
            self.instruction_font_size,
            anchor_x="center",
            anchor_y="center"
        )
        
        # 绘制左侧牌库
        self._draw_card_library()
        
        # 绘制右侧卡组
        self._draw_current_deck()
        
        # 绘制滚动条（替换原来的分隔线）
        self._draw_scrollbar()
        
        # 绘制卡组统计信息
        self._draw_deck_stats()
        
        # 绘制悬停卡牌的详细信息（tooltip）
        if self.tooltip_card:
            self._draw_card_tooltip(self.tooltip_card, self.tooltip_x, self.tooltip_y)
    
    def _draw_scrollbar(self):
        """绘制滚动条（替换原来的分隔线）"""
        # 滚动条位置（向右移动300px：居中位置+200px+再右移100px）
        divider_x = (self.left_panel_x + self.right_panel_x) / 2 + S.px(300)
        
        # 滚动条背景
        scrollbar_top = self.window.height - S.py(150)
        scrollbar_bottom = S.py(150)
        scrollbar_height = scrollbar_top - scrollbar_bottom
        
        # 绘制滚动条轨道
        arcade.draw_lrbt_rectangle_filled(
            divider_x - self.scrollbar_width / 2,
            divider_x + self.scrollbar_width / 2,
            scrollbar_bottom,
            scrollbar_top,
            self.scrollbar_color
        )
        
        # 绘制滚动条边框
        arcade.draw_lrbt_rectangle_outline(
            divider_x - self.scrollbar_width / 2,
            divider_x + self.scrollbar_width / 2,
            scrollbar_bottom,
            scrollbar_top,
            arcade.color.GRAY,
            S.scale(2)
        )
        
        # 计算滚动条滑块位置
        all_cards = self._get_all_available_cards()
        cards_per_row = 4
        total_rows = (len(all_cards) + cards_per_row - 1) // cards_per_row
        max_rows = self.max_library_visible_rows
        
        if total_rows > max_rows:
            handle_height = (max_rows / total_rows) * scrollbar_height
            handle_height = max(handle_height, S.py(30))  # 最小滑块高度
            
            # 计算滑块位置
            scroll_ratio = self.library_scroll_offset / (total_rows - max_rows)
            handle_y = scrollbar_bottom + (scrollbar_height - handle_height) * (1 - scroll_ratio)
            
            # 绘制滑块
            arcade.draw_lrbt_rectangle_filled(
                divider_x - self.scrollbar_width / 2 + S.scale(2),
                divider_x + self.scrollbar_width / 2 - S.scale(2),
                handle_y,
                handle_y + handle_height,
                self.scrollbar_handle_color
            )
    
    def _draw_card_library(self):
        """绘制左侧牌库区域"""
        # 获取所有可用卡牌（从玩家的完整卡池中）
        all_cards = self._get_all_available_cards()
        
        if not all_cards:
            return
        
        # 标题
        library_title_y = self.window.height - S.py(120)
        arcade.draw_text(
            "牌库",
            self.left_panel_x + S.px(100),
            library_title_y,
            arcade.color.LIGHT_BLUE,
            S.font(24),
            anchor_x="left",
            anchor_y="center",
            bold=True
        )
        
        # 计算卡牌网格布局（4列3行，向下移动70px）
        start_x = self.left_panel_x + S.px(20)
        start_y = library_title_y - S.py(150)  # 原80，向下移动70px变为150
        cards_per_row = 4  # 四列布局
        row_spacing = self.card_height + S.py(20)
        col_spacing = self.card_width + self.card_spacing
        
        # 计算可见卡牌范围（考虑滚动）
        total_rows = (len(all_cards) + cards_per_row - 1) // cards_per_row
        max_visible_cards = self.max_library_visible_rows * cards_per_row
        visible_start = self.library_scroll_offset * cards_per_row
        visible_end = min(len(all_cards), visible_start + max_visible_cards)
        visible_cards = all_cards[visible_start:visible_end]
        
        for i, card in enumerate(visible_cards):
            row = i // cards_per_row
            col = i % cards_per_row
            
            card_x = start_x + col * col_spacing + self.card_width / 2
            card_y = start_y - row * row_spacing
            
            # 检查是否悬停
            is_hovered = (i == self.hovered_card_index)
            
            # 绘制卡牌
            self._draw_library_card(card, card_x, card_y, is_hovered)
    
    def _draw_library_card(self, card: Card, x: float, y: float, is_hovered: bool):
        """绘制牌库中的卡牌（完整版，包含卡图）"""
        half_width = self.card_width / 2
        half_height = self.card_height / 2
        
        # 根据稀有度设置背景色
        rarity_color = RARITY_COLORS.get(card.rarity, arcade.color.WHITE)
        
        # 悬停效果 - 修复透明度处理
        if is_hovered:
            bg_color = (*rarity_color[:3], 255)  # 完全不透明，增强悬停效果
            border_width = S.scale(4)
        else:
            bg_color = (*rarity_color[:3], 180)
            border_width = S.scale(2)
        
        # 绘制背景
        arcade.draw_lrbt_rectangle_filled(
            x - half_width, x + half_width,
            y - half_height, y + half_height,
            bg_color
        )
        
        # 绘制边框
        border_colors = [arcade.color.BLACK, arcade.color.SKY_BLUE, 
                        arcade.color.INDIGO, arcade.color.GOLD]
        border_color = border_colors[card.rarity.value] if card.rarity.value < len(border_colors) else arcade.color.WHITE
        
        arcade.draw_lrbt_rectangle_outline(
            x - half_width, x + half_width,
            y - half_height, y + half_height,
            border_color,
            border_width
        )
        
        # 绘制卡牌内容（完整版，包含卡图）
        self._draw_library_card_content(card, x, y)
    
    def _draw_library_card_content(self, card: Card, x: float, y: float):
        """绘制牌库卡牌内容（完整版，包含卡图）"""
        half_width = self.card_width / 2
        half_height = self.card_height / 2
        
        # 卡图区域（上半部分）
        image_width = int(self.card_width - S.px(20))
        image_height = S.py(150)
        image_x = x
        image_y = y + half_height - S.py(30) - image_height / 2
        
        # 尝试绘制卡图，如果没有则显示问号
        self._draw_card_image_with_placeholder(card, image_x, image_y, image_width, image_height)
        
        # 卡牌名称（图像下方）
        name_y = image_y - image_height / 2 - S.py(25)
        max_name_width = int(self.card_width - S.px(20))
        
        processed_name = prepare_text_for_arcade(
            card.name,
            max_width=max_name_width,
            font_size=S.font(16)
        )
        
        arcade.draw_text(
            processed_name,
            x, name_y,
            arcade.color.WHITE,
            S.font(16),
            anchor_x="center",
            anchor_y="top",
            bold=True,
            multiline=True,
            width=max_name_width
        )
        
        # AP/MP消耗（靠左显示）
        cost_x = x - half_width + S.px(15)
        cost_y = name_y - S.py(30)
        cost_text = f"AP:{card.ap_cost}"
        if hasattr(card, 'mp_cost') and card.mp_cost > 0:
            cost_text += f" MP:{card.mp_cost}"
        
        arcade.draw_text(
            cost_text,
            cost_x, cost_y,
            arcade.color.YELLOW,
            S.font(14),
            anchor_x="left",
            anchor_y="top"
        )
        
        # 稀有度
        rarity_names = ["普通", "优秀", "稀有", "传说"]
        rarity_name = rarity_names[card.rarity.value] if card.rarity.value < len(rarity_names) else "未知"
        rarity_colors_list = [arcade.color.GRAY, arcade.color.SKY_BLUE, 
                             arcade.color.INDIGO, arcade.color.GOLD]
        rarity_color = rarity_colors_list[card.rarity.value] if card.rarity.value < len(rarity_colors_list) else arcade.color.WHITE
        
        rarity_x = x - half_width + S.px(15)
        rarity_y = cost_y - S.py(25)
        arcade.draw_text(
            rarity_name,
            rarity_x, rarity_y,
            rarity_color,
            S.font(14),
            anchor_x="left",
            anchor_y="top",
            bold=True
        )
    
    def _draw_card_image_with_placeholder(self, card: Card, x: float, y: float, width: float, height: float):
        """绘制卡牌图片，如果没有则显示问号占位符"""
        # 尝试获取卡图
        image_path = None
        try:
            # 根据卡牌名称尝试查找图片
            image_name = card.name.replace(" ", "_").lower()
            # 检查assets目录
            import os
            possible_paths = [
                f"assets/{image_name}.png",
                f"assets/{image_name}.jpg",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    image_path = path
                    break
        except:
            pass
        
        # 绘制卡图或占位符
        if image_path:
            try:
                texture = arcade.load_texture(image_path)
                arcade.draw_texture_rectangle(
                    x, y,
                    width, height,
                    texture
                )
            except:
                # 如果加载失败，显示占位符
                self._draw_card_placeholder(x, y, width, height)
        else:
            # 没有卡图，显示问号占位符
            self._draw_card_placeholder(x, y, width, height)
    
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
            S.scale(2)
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
    
    def _draw_current_deck(self):
        """绘制右侧当前卡组区域"""
        # 标题
        deck_title_y = self.window.height - S.py(120)
        arcade.draw_text(
            f"当前卡组 ({len(self.player.deck)}张)",
            self.right_panel_x + S.px(20),
            deck_title_y,
            arcade.color.LIGHT_GREEN,
            S.font(24),
            anchor_x="left",
            anchor_y="center",
            bold=True
        )
        
        # 绘制卡组中的卡牌（长条形式）
        start_y = deck_title_y - S.py(70)
        card_spacing_y = self.deck_card_height + S.py(10)
        
        # 考虑滚动
        visible_start = max(0, self.deck_scroll_offset)
        visible_end = min(len(self.player.deck), visible_start + 12)  # 最多显示12张
        
        for i in range(visible_start, visible_end):
            card = self.player.deck[i]
            card_y = start_y - (i - visible_start) * card_spacing_y
            
            # 检查是否悬停 - 修复索引计算
            display_index = i - visible_start
            is_hovered = (display_index == self.hovered_deck_card_index)
            is_selected = (i == self.selected_card_index)
            
            # 绘制长条卡牌
            self._draw_deck_card_strip(card, self.right_panel_x + S.px(20), card_y, is_hovered, is_selected)
    
    def _draw_deck_card_strip(self, card: Card, x: float, y: float, is_hovered: bool, is_selected: bool):
        """绘制卡组中的长条卡牌"""
        half_width = self.deck_card_width / 2
        half_height = self.deck_card_height / 2
        
        # 根据状态确定颜色
        if is_selected:
            bg_color = (100, 50, 50, 200)  # 红色背景表示待删除
            border_color = arcade.color.RED
            border_width = S.scale(3)
        elif is_hovered:
            bg_color = (80, 80, 100, 200)  # 高亮背景
            border_color = arcade.color.YELLOW
            border_width = S.scale(3)
        else:
            bg_color = (40, 40, 50, 200)  # 普通背景
            border_color = arcade.color.WHITE
            border_width = S.scale(2)
        
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
        
        # 左侧：AP/MP消耗
        cost_x = x - half_width + S.px(40)
        cost_text = f"{card.ap_cost}AP"
        if hasattr(card, 'mp_cost') and card.mp_cost > 0:
            cost_text += f"/{card.mp_cost}MP"
        
        arcade.draw_text(
            cost_text,
            cost_x, y,
            arcade.color.YELLOW,
            S.font(16),
            anchor_x="left",
            anchor_y="center",
            bold=True
        )
        
        # 右侧：卡牌名称
        name_x = x + half_width - S.px(20)
        max_name_width = int(self.deck_card_width - S.px(120))
        
        processed_name = prepare_text_for_arcade(
            card.name,
            max_width=max_name_width,
            font_size=S.font(18)
        )
        
        arcade.draw_text(
            processed_name,
            name_x, y + S.py(8),
            arcade.color.WHITE,
            S.font(18),
            anchor_x="right",
            anchor_y="center",
            bold=True,
            multiline=True,
            width=max_name_width
        )
        
        # 卡图中间位置（在名字下方画一条短线表示卡图位置）
        image_indicator_y = y - S.py(12)
        arcade.draw_line(
            name_x - S.px(60), image_indicator_y,
            name_x - S.px(20), image_indicator_y,
            arcade.color.GRAY,
            S.scale(2)
        )
    
    def _draw_card_tooltip(self, card: Card, x: float, y: float):
        """绘制卡牌详细信息tooltip"""
        tooltip_width = S.px(350)
        tooltip_height = S.py(250)
        padding = S.px(15)
        
        # 确保tooltip不超出屏幕
        tooltip_x = min(x + S.px(20), self.window.width - tooltip_width - S.px(20))
        tooltip_y = max(y - tooltip_height / 2, S.py(50))
        
        # 绘制背景
        arcade.draw_lrbt_rectangle_filled(
            tooltip_x, tooltip_x + tooltip_width,
            tooltip_y, tooltip_y + tooltip_height,
            (30, 30, 40, 240)
        )
        
        # 绘制边框
        arcade.draw_lrbt_rectangle_outline(
            tooltip_x, tooltip_x + tooltip_width,
            tooltip_y, tooltip_y + tooltip_height,
            arcade.color.GOLD,
            S.scale(3)
        )
        
        # 绘制内容
        content_x = tooltip_x + padding
        content_y = tooltip_y + tooltip_height - padding
        
        # 卡牌名称
        processed_name = prepare_text_for_arcade(
            card.name,
            max_width=int(tooltip_width - padding * 2),
            font_size=S.font(22)
        )
        
        arcade.draw_text(
            processed_name,
            content_x + (tooltip_width - padding * 2) / 2,
            content_y,
            arcade.color.GOLD,
            S.font(22),
            anchor_x="center",
            anchor_y="top",
            bold=True,
            multiline=True,
            width=int(tooltip_width - padding * 2)
        )
        
        content_y -= S.py(35)
        
        # AP/MP消耗
        cost_text = f"AP消耗: {card.ap_cost}"
        if hasattr(card, 'mp_cost') and card.mp_cost > 0:
            cost_text += f" | MP消耗: {card.mp_cost}"
        
        arcade.draw_text(
            cost_text,
            content_x,
            content_y,
            arcade.color.YELLOW,
            S.font(16),
            anchor_x="left",
            anchor_y="top"
        )
        
        content_y -= S.py(30)
        
        # 稀有度
        rarity_names = ["普通", "优秀", "稀有", "传说"]
        rarity_name = rarity_names[card.rarity.value] if card.rarity.value < len(rarity_names) else "未知"
        rarity_colors_list = [arcade.color.GRAY, arcade.color.SKY_BLUE, 
                             arcade.color.INDIGO, arcade.color.GOLD]
        rarity_color = rarity_colors_list[card.rarity.value] if card.rarity.value < len(rarity_colors_list) else arcade.color.WHITE
        
        arcade.draw_text(
            f"稀有度: {rarity_name}",
            content_x,
            content_y,
            rarity_color,
            S.font(16),
            anchor_x="left",
            anchor_y="top"
        )
        
        content_y -= S.py(30)
        
        # 卡牌描述
        description = getattr(card, 'description', '') or getattr(card, 'desc', '') or "无描述"
        processed_desc = prepare_text_for_arcade(
            description,
            max_width=int(tooltip_width - padding * 2),
            font_size=S.font(15)
        )
        
        arcade.draw_text(
            processed_desc,
            content_x,
            content_y,
            arcade.color.WHITE,
            S.font(15),
            anchor_x="left",
            anchor_y="top",
            multiline=True,
            width=int(tooltip_width - padding * 2)
        )
        
        content_y -= S.py(80)
        
        # 预计效果（如果有战斗系统引用）
        expected_values = self._calculate_expected_values(card)
        if expected_values:
            arcade.draw_text(
                "预计效果:",
                content_x,
                content_y,
                arcade.color.LIGHT_GREEN,
                S.font(16),
                anchor_x="left",
                anchor_y="top",
                bold=True
            )
            
            content_y -= S.py(25)
            for value_text in expected_values:
                arcade.draw_text(
                    f"• {value_text}",
                    content_x,
                    content_y,
                    arcade.color.WHITE,
                    S.font(14),
                    anchor_x="left",
                    anchor_y="top"
                )
                content_y -= S.py(20)
    
    def _calculate_expected_values(self, card: Card) -> list:
        """
        计算卡牌的预期效果数值
        
        Args:
            card: 卡牌对象
        
        Returns:
            描述列表，如 ["伤害: 15-20", "格挡: 10"]
        """
        expected = []
        
        # 获取当前实体（用于计算属性加值）
        current_entity = self.player
        
        # 计算属性加值（如果有实体且卡牌有stat_ratios）
        stat_bonus = 0
        if current_entity and hasattr(card, 'stat_ratios') and card.stat_ratios:
            stat_bonus = card.get_stat_bonus(current_entity.stats)
        
        # 处理结构化效果列表
        if isinstance(card.effects, list):
            for effect in card.effects:
                effect_type = effect.get("type", "")
                
                # 敌方伤害效果
                if effect_type == "emy_dmg":
                    dice_expr = effect.get("dice", "")
                    if dice_expr:
                        # 解析骰子表达式
                        try:
                            parts = dice_expr.lower().split('d')
                            if len(parts) == 2:
                                num_dice = int(parts[0])
                                sides = int(parts[1])
                                min_damage = num_dice + stat_bonus
                                max_damage = num_dice * sides + stat_bonus
                                expected.append(f"伤害: {min_damage}-{max_damage} ({dice_expr}{f'+{stat_bonus}' if stat_bonus != 0 else ''})")
                        except:
                            expected.append(f"伤害: {dice_expr}")
                
                # 自我治疗
                elif effect_type == "self_heal":
                    dice_expr = effect.get("dice", "")
                    if dice_expr:
                        try:
                            parts = dice_expr.lower().split('d')
                            if len(parts) == 2:
                                num_dice = int(parts[0])
                                sides = int(parts[1])
                                min_heal = num_dice + stat_bonus
                                max_heal = num_dice * sides + stat_bonus
                                expected.append(f"治疗: {min_heal}-{max_heal} ({dice_expr}{f'+{stat_bonus}' if stat_bonus != 0 else ''})")
                        except:
                            expected.append(f"治疗: {dice_expr}")
                    else:
                        amount = effect.get("amount", 0)
                        if isinstance(amount, (int, float)):
                            actual_amount = amount + stat_bonus
                            expected.append(f"治疗: {actual_amount}")
                
                # 自我格挡
                elif effect_type == "self_block":
                    dice_expr = effect.get("dice", "")
                    if dice_expr:
                        try:
                            parts = dice_expr.lower().split('d')
                            if len(parts) == 2:
                                num_dice = int(parts[0])
                                sides = int(parts[1])
                                min_block = num_dice + stat_bonus
                                max_block = num_dice * sides + stat_bonus
                                expected.append(f"格挡: {min_block}-{max_block} ({dice_expr}{f'+{stat_bonus}' if stat_bonus != 0 else ''})")
                        except:
                            expected.append(f"格挡: {dice_expr}")
                    else:
                        amount = effect.get("amount", 0)
                        if isinstance(amount, (int, float)):
                            actual_amount = amount + stat_bonus
                            expected.append(f"格挡: {actual_amount}")
                
                # 敌方Debuff
                elif effect_type == "emy_debuff":
                    buff_type = effect.get("buff_type", "")
                    stacks = effect.get("stacks", 1)
                    expected.append(f"施加 {stacks} 层 {buff_type}")
                
                # 自我Buff
                elif effect_type == "self_buff":
                    buff_type = effect.get("buff_type", "")
                    stacks = effect.get("stacks", 1)
                    expected.append(f"获得 {stacks} 层 {buff_type}")
        
        # 如果没有结构化效果，尝试旧格式
        elif isinstance(card.effects, dict):
            if "hp" in card.effects:
                hp_change = card.effects["hp"]
                if hp_change < 0:
                    damage = abs(hp_change) + stat_bonus
                    expected.append(f"伤害: {damage}")
                elif hp_change > 0:
                    heal = hp_change + stat_bonus
                    expected.append(f"治疗: {heal}")
            
            if "block" in card.effects:
                block = card.effects["block"] + stat_bonus
                expected.append(f"格挡: {block}")
        
        return expected
    
    def _draw_deck_stats(self):
        """绘制卡组统计信息"""
        stats_x = self.right_panel_x + S.px(20)
        stats_y = S.py(80)
        
        # 卡组大小提示（编辑时不显示警告，只在退出时验证）
        deck_size = len(self.player.deck)
        min_size = 12
        max_size = 28
        
        # 编辑过程中只显示当前大小，不显示警告
        color = arcade.color.WHITE
        status = f"卡组大小: {deck_size}张 (要求: {min_size}-{max_size}张)"
        
        arcade.draw_text(
            status,
            stats_x, stats_y,
            color,
            S.font(18),
            anchor_x="left",
            anchor_y="center",
            bold=True
        )
        
        # 稀有度分布
        rarity_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for card in self.player.deck:
            if card.rarity.value in rarity_counts:
                rarity_counts[card.rarity.value] += 1
        
        rarity_names = ["普通", "优秀", "稀有", "传说"]
        rarity_colors_list = [arcade.color.GRAY, arcade.color.SKY_BLUE, 
                             arcade.color.INDIGO, arcade.color.GOLD]
        
        stats_y -= S.py(30)
        for i, (rarity_val, count) in enumerate(rarity_counts.items()):
            color = rarity_colors_list[i]
            name = rarity_names[i]
            
            arcade.draw_text(
                f"{name}: {count}",
                stats_x + i * S.px(100), stats_y,
                color,
                S.font(16),
                anchor_x="left",
                anchor_y="center"
            )
    
    def _get_all_available_cards(self) -> List[Card]:
        """获取所有可用卡牌（从玩家的牌库）"""
        # 优先使用玩家的牌库系统
        if hasattr(self.player, 'card_library') and self.player.card_library:
            # 只获取牌库中实际存在的卡牌（排除已达上限的）
            available_cards = self.player.card_library.get_available_cards_for_deck()
            if available_cards:  # 如果牌库中有可用卡牌，直接返回
                print(f"[DEBUG] 从牌库获取 {len(available_cards)} 张可用卡牌")
                return available_cards
            else:
                print(f"[DEBUG] 牌库中没有可用卡牌")
                return []
        
        # 如果牌库为空或不存在，返回空列表
        # 不再从卡组推断，因为那些卡牌不在牌库中，无法添加
        print("[DEBUG] 牌库系统不存在或为空")
        return []
    
    def _can_add_card(self, card: Card) -> bool:
        """检查是否可以添加卡牌到卡组"""
        # 如果玩家有牌库系统，使用牌库的检查方法
        if hasattr(self.player, 'card_library') and self.player.card_library:
            return self.player.card_library.can_add_to_deck(card.name)
        
        # 否则使用原有的逻辑（向后兼容）
        # 检查卡组大小限制
        if len(self.player.deck) >= 28:
            return False
        
        # 检查同名卡牌数量限制
        card_name = card.name
        current_count = self.deck_card_counts.get(card_name, 0)
        
        # 四种稀有度的上限：普通3/优秀2/稀有2/传说1
        max_counts = {
            Rarity.COMMON: 3,
            Rarity.UNCOMMON: 2,
            Rarity.RARE: 2,
            Rarity.LEGENDARY: 1
        }
        
        max_count = max_counts.get(card.rarity, 1)
        
        if current_count >= max_count:
            print(f"无法添加：同名卡牌已达上限 ({current_count}/{max_count})")
            return False
        
        return True
    
    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """鼠标移动事件 - 使用Sprite进行碰撞检测"""
        # 重置tooltip和悬停索引
        self.tooltip_card = None
        self.hovered_card_index = -1
        self.hovered_deck_card_index = -1
        
        # 更新Sprite列表（确保位置正确）
        self._update_card_sprites()
        
        # 使用Sprite的碰撞检测方法
        mouse_point = (x, y)
        
        # 检查牌库卡牌
        library_hits = arcade.get_sprites_at_point(mouse_point, self.library_card_sprites)
        if library_hits:
            # 获取第一个命中的Sprite
            hit_sprite = library_hits[0]
            sprite_index = self.library_card_sprites.index(hit_sprite)
            map_key = f"library_{sprite_index}"
            
            if map_key in self.card_sprite_map:
                area_type, card_index = self.card_sprite_map[map_key]
                if area_type == 'library':
                    self.hovered_card_index = card_index
                    
                    # 获取对应的卡牌对象
                    all_cards = self._get_all_available_cards()
                    if card_index < len(all_cards):
                        self.tooltip_card = all_cards[card_index]
                        self.tooltip_x = x
                        self.tooltip_y = y
        
        # 如果没有悬停牌库，检查组卡牌
        if self.tooltip_card is None:
            deck_hits = arcade.get_sprites_at_point(mouse_point, self.deck_card_sprites)
            if deck_hits:
                # 获取第一个命中的Sprite
                hit_sprite = deck_hits[0]
                sprite_index = self.deck_card_sprites.index(hit_sprite)
                map_key = f"deck_{sprite_index}"
                
                if map_key in self.card_sprite_map:
                    area_type, card_index = self.card_sprite_map[map_key]
                    if area_type == 'deck':
                        # 计算相对于可见区域的索引
                        visible_start = max(0, self.deck_scroll_offset)
                        self.hovered_deck_card_index = card_index - visible_start
                        
                        # 获取对应的卡牌对象
                        if card_index < len(self.player.deck):
                            self.tooltip_card = self.player.deck[card_index]
                            self.tooltip_x = x
                            self.tooltip_y = y
        
        # 调试输出：显示当前悬停状态
        if self.hovered_card_index >= 0 or self.hovered_deck_card_index >= 0:
            print(f"[DEBUG HOVER] 牌库索引: {self.hovered_card_index}, 卡组索引: {self.hovered_deck_card_index}")
    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """鼠标点击事件"""
        if self.selection_completed:
            return
        
        print(f"[DEBUG CLICK] 位置: ({x:.0f}, {y:.0f}), 牌库索引: {self.hovered_card_index}, 卡组索引: {self.hovered_deck_card_index}")
        
        # 点击牌库中的卡牌 - 添加到卡组（考虑滚动和4列布局）
        if self.hovered_card_index >= 0:
            all_cards = self._get_all_available_cards()
            cards_per_row = 4
            max_visible_cards = self.max_library_visible_rows * cards_per_row
            visible_start = self.library_scroll_offset * cards_per_row
            visible_end = min(len(all_cards), visible_start + max_visible_cards)
            
            print(f"[DEBUG] 点击牌库卡牌，悬停索引: {self.hovered_card_index}")
            print(f"[DEBUG] 可见范围: {visible_start}-{visible_end}")
            
            if self.hovered_card_index < visible_end:
                card = all_cards[self.hovered_card_index]
                
                # 如果玩家有牌库系统，使用牌库的方法添加
                if hasattr(self.player, 'card_library') and self.player.card_library:
                    # 找到卡牌在牌库中的索引
                    library_cards = self.player.card_library.get_cards_by_name(card.name)
                    if library_cards:
                        # 使用第一个可用的副本
                        if self.player.card_library.add_card_to_deck(card.name):
                            # 更新计数和Sprite
                            self._update_deck_card_counts()
                            self._update_card_sprites()
                            print(f"已添加卡牌: {card.name}")
                        else:
                            print("无法添加此卡牌（已达上限或卡组已满）")
                    else:
                        print(f"[提示] {card.name} 不在你的牌库中，无法添加")
                        print(f"[提示] 该卡牌仅显示在卡组中，请先确保卡牌已收藏到牌库")
                else:
                    # 原有逻辑（向后兼容）
                    if self._can_add_card(card):
                        # 创建卡牌副本并添加到卡组
                        new_card = card.copy()
                        new_card.owner = self.player
                        self.player.deck.append(new_card)
                        
                        # 更新计数
                        self._update_deck_card_counts()
                        self._update_card_sprites()
                        print(f"已添加卡牌: {card.name}")
                    else:
                        print("无法添加此卡牌（已达上限或卡组已满）")
        
        # 点击卡组中的卡牌 - 删除并返回牌库
        elif self.hovered_deck_card_index >= 0:
            visible_start = max(0, self.deck_scroll_offset)
            actual_index = visible_start + self.hovered_deck_card_index
            
            if actual_index < len(self.player.deck):
                # 如果玩家有牌库系统，使用牌库的方法删除
                if hasattr(self.player, 'card_library') and self.player.card_library:
                    removed_card = self.player.card_library.remove_card_from_deck(actual_index)
                    if removed_card:
                        self._update_deck_card_counts()
                        self._update_card_sprites()
                        print(f"已删除卡牌: {removed_card.name} 并返回牌库")
                    else:
                        # 给出更详细的提示信息
                        print("无法删除卡牌（索引无效）")
                else:
                    # 原有逻辑（向后兼容）
                    removed_card = self.player.deck.pop(actual_index)
                    self._update_deck_card_counts()
                    self._update_card_sprites()
                    print(f"已删除卡牌: {removed_card.name}")
    
    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        """鼠标滚轮事件 - 支持牌库和卡组滚动"""
        # 检查鼠标是否在牌库区域（考虑新的位置，向下移动70px）
        library_title_y = self.window.height - S.py(120)
        start_x = self.left_panel_x + S.px(20)
        start_y = library_title_y - S.py(150)  # 向下移动70px
        
        # 牌库区域范围
        library_bottom = start_y - self.max_library_visible_rows * (self.card_height + S.py(20))
        
        if start_x <= x <= self.right_panel_x and library_bottom <= y <= library_title_y:
            # 在牌库区域滚动
            all_cards = self._get_all_available_cards()
            cards_per_row = 4
            total_rows = (len(all_cards) + cards_per_row - 1) // cards_per_row
            max_rows = self.max_library_visible_rows
            
            if scroll_y > 0:
                # 向上滚动
                self.library_scroll_offset = max(0, self.library_scroll_offset - 1)
            elif scroll_y < 0:
                # 向下滚动
                max_offset = max(0, total_rows - max_rows)
                self.library_scroll_offset = min(max_offset, self.library_scroll_offset + 1)
            
            # 更新Sprite列表
            self._update_card_sprites()
        else:
            # 在卡组区域滚动
            if scroll_y > 0:
                self.deck_scroll_offset = max(0, self.deck_scroll_offset - 1)
            elif scroll_y < 0:
                max_offset = max(0, len(self.player.deck) - 12)
                self.deck_scroll_offset = min(max_offset, self.deck_scroll_offset + 1)
            
            # 更新Sprite列表
            self._update_card_sprites()
    
    def on_key_press(self, key: int, modifiers: int):
        """键盘事件"""
        if key == arcade.key.ESCAPE:
            # 退出编辑前验证卡组
            if hasattr(self.player, 'card_library') and self.player.card_library:
                is_valid, errors = self.player.card_library.validate_deck_for_battle()
                
                if not is_valid:
                    print(f"\n[WARNING] 卡组验证失败：")
                    for error in errors:
                        print(f"  - {error}")
                    print(f"\n请调整卡组后再退出编辑（按ESC重新编辑）")
                    return  # 不退出，让玩家继续编辑
                else:
                    print(f"\n[OK] 卡组验证通过！")
            
            # 完成编辑
            self.selection_completed = True
            self.on_edit_complete()
            
            # 注意：不再自动返回GameView，让回调函数决定下一步显示什么视图
            # 回调函数会调用 _end_battle_and_start_narrative() 进入叙事场景
            print(f"[DEBUG] DeckEditView ESC退出，等待回调函数处理下一步")

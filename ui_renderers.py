"""
UI渲染器模块
负责所有绘制相关的功能
"""
import arcade
from typing import Dict, Optional
from models import Entity, Card
from battle_system import BattleSystem
from config import CONSTANTS, CARD_TYPE_NAMES, RARITY_COLORS, TargetType
from tile_map import TileMap
from ui_scale import S


class UIRenderer:
    """UI渲染器 - 处理所有绘制逻辑"""
    
    def __init__(self, window_width: int, window_height: int):
        self.window_width = window_width
        self.window_height = window_height
        
        # 字体大小（通过全局缩放单例计算，自动适应 4K/高 DPI 屏幕）
        self.headtitle_font_size = S.font(24)
        self.title_font_size = S.font(18)
        self.text_font_size = S.font(12)
        self.number_font_size = S.font(18)
        self.normal_font_size = S.font(16)
        
        # 文本对象缓存
        self.text_objects: Dict[str, arcade.Text] = {}
        
        # 加载图片素材
        self._load_textures()
    
    def on_resize(self, width: int, height: int):
        """窗口尺寸变化时更新内部状态（S 已由 CardGame.on_resize 刷新）。"""
        self.window_width = width
        self.window_height = height
        # 重新计算字体大小
        self.headtitle_font_size = S.font(24)
        self.title_font_size = S.font(18)
        self.text_font_size = S.font(12)
        self.number_font_size = S.font(18)
        self.normal_font_size = S.font(16)
        # 清除文本缓存，使字体大小立即生效
        self.text_objects.clear()
    
    def _load_textures(self):
        """加载图片素材"""
        import os
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
        try:
            self.ap_16_texture = arcade.load_texture(os.path.join(assets_dir, 'ap_16.png'))
            self.ap_32_texture = arcade.load_texture(os.path.join(assets_dir, 'ap_32.png'))
            self.card_test_texture = arcade.load_texture(os.path.join(assets_dir, 'card_test.png'))
            self.phy_texture = arcade.load_texture(os.path.join(assets_dir, 'phy.png'))
            self.def_texture = arcade.load_texture(os.path.join(assets_dir, 'def.png'))
        except Exception as e:
            print(f"警告: 无法加载部分图片素材: {e}")
            self.ap_16_texture = None
            self.ap_32_texture = None
            self.card_test_texture = None
            self.phy_texture = None
            self.def_texture = None
    
    def draw_text(self, text: str, x: float, y: float, color, font_size: int, 
                  anchor_x: str = "left", anchor_y: str = "baseline", bold: bool = False,
                  multiline: bool = False, width: int = None):
        """绘制文本的辅助方法，使用Text对象提高性能"""
        cache_key = f"{text}_{x}_{y}_{font_size}_{bold}"
        
        if cache_key not in self.text_objects:
            try:
                text_obj = arcade.Text(
                    text=text,
                    x=x,
                    y=y,
                    color=color,
                    font_size=font_size,
                    anchor_x=anchor_x,
                    anchor_y=anchor_y,
                    bold=bold,
                    multiline=multiline,
                    width=width
                )
                self.text_objects[cache_key] = text_obj
            except TypeError:
                arcade.draw_text(
                    text, x, y, color, font_size,
                    anchor_x=anchor_x, anchor_y=anchor_y,
                    bold=bold, multiline=multiline, width=width
                )
                return
        
        text_obj = self.text_objects[cache_key]
        text_obj.text = text
        text_obj.x = x
        text_obj.y = y
        text_obj.color = color
        text_obj.font_size = font_size
        text_obj.anchor_x = anchor_x
        text_obj.anchor_y = anchor_y
        text_obj.bold = bold
        text_obj.draw()
    
    def cleanup_text_cache(self):
        """清理过期的Text对象（防止内存泄漏）"""
        if len(self.text_objects) > 100:
            keys = list(self.text_objects.keys())
            for key in keys[:-50]:
                del self.text_objects[key]
    
    def draw_tile_map(self, tile_map: TileMap, map_offset_x: float, map_offset_y: float,
                     battle: BattleSystem, entity_positions: Dict[Entity, tuple]):
        """
        绘制瓦片地图和实体
        
        Args:
            tile_map: 瓦片地图对象
            map_offset_x, map_offset_y: 地图偏移量（已废弃，保留兼容性）
            battle: 战斗系统
            entity_positions: 实体位置字典
        """
        # 绘制所有瓦片（直接使用世界坐标，不再需要偏移量）
        for y in range(tile_map.height):
            for x in range(tile_map.width):
                tile = tile_map.get_tile(x, y)
                if tile:
                    pixel_x, pixel_y = tile_map.get_tile_pixel_pos(x, y)
                    half_size = tile_map.tile_size / 2
                    
                    arcade.draw_lrbt_rectangle_filled(
                        pixel_x - half_size, pixel_x + half_size,
                        pixel_y - half_size, pixel_y + half_size,
                        tile.color
                    )
                    
                    arcade.draw_lrbt_rectangle_outline(
                        pixel_x - half_size, pixel_x + half_size,
                        pixel_y - half_size, pixel_y + half_size,
                        arcade.color.BLACK, 1
                    )
        
        # 保存实体位置映射并绘制所有实体
        entity_positions.clear()
        
        # 绘制玩家队伍
        for entity in battle.player_team:
            if entity.is_alive():
                entity_x, entity_y = tile_map.get_tile_pixel_pos(*entity.position)
                entity_positions[entity] = (entity_x, entity_y)
                
                color = arcade.color.BLUE if entity.control_type.value == "player" else arcade.color.CYAN
                arcade.draw_circle_filled(entity_x, entity_y, 15, color)
                arcade.draw_circle_outline(entity_x, entity_y, 15, arcade.color.WHITE, 2)
        
        # 绘制敌人队伍
        for entity in battle.enemy_team:
            if entity.is_alive():
                entity_x, entity_y = tile_map.get_tile_pixel_pos(*entity.position)
                entity_positions[entity] = (entity_x, entity_y)
                
                arcade.draw_circle_filled(entity_x, entity_y, 15, arcade.color.RED)
                arcade.draw_circle_outline(entity_x, entity_y, 15, arcade.color.WHITE, 2)
    
    def draw_battle_info(self, battle: BattleSystem):
        """绘制战斗信息（血条、AP等）"""
        status = battle.get_battle_status()
        
        top_margin = S.py(50)
        bar_y_start = self.window_height - top_margin
        bar_height = S.py(25)
        
        # 回合数
        current_entity_name = status.get('current_entity', '未知')
        self.draw_text(
            f"第{battle.current_round}回合 - {current_entity_name}",
            self.window_width / 2,
            self.window_height - 30,
            arcade.color.BLACK,
            self.headtitle_font_size,
            anchor_x="center", anchor_y="center", bold=True
        )
        
        player_entities = [e for e in battle.player_team if e.is_alive()]
        enemy_entities = [e for e in battle.enemy_team if e.is_alive()]
        
        max_entities_per_side = max(len(player_entities), len(enemy_entities), 1)
        bar_width_per_entity = (self.window_width // 4) // max_entities_per_side
        
        # 绘制玩家队伍血条
        for i, entity in enumerate(player_entities):
            self._draw_entity_health_bar(entity, i, bar_width_per_entity, 
                                        bar_y_start, bar_height, True)
        
        # 绘制敌人队伍血条
        for i, entity in enumerate(enemy_entities):
            self._draw_entity_health_bar(entity, i, bar_width_per_entity,
                                        bar_y_start, bar_height, False)
        
        # AP显示
        self._draw_ap_display(battle)
        
        # MP显示
        self._draw_mp_display(battle)
        
        # 绘制卡组和弃牌堆数量
        self._draw_deck_info(battle)
    
    def _draw_entity_health_bar(self, entity: Entity, index: int, bar_width: float,
                               bar_y_start: float, bar_height: float, is_player: bool):
        """绘制单个实体的血条（包含职业信息）"""
        entity_bar_width = bar_width * 0.8
        
        if is_player:
            entity_bar_x = (self.window_width // 8) + index * bar_width
        else:
            entity_bar_x = self.window_width - (self.window_width // 8) - index * bar_width
        
        # 检查是否有职业，有职业则增加血条高度
        has_career = hasattr(entity, 'career') and entity.career is not None
        career_height_offset = bar_height * 0.5 if has_career else 0
        total_height = bar_height + career_height_offset
        
        # 血条背景
        arcade.draw_lrbt_rectangle_filled(
            entity_bar_x - entity_bar_width / 2, entity_bar_x + entity_bar_width / 2,
            bar_y_start - total_height * 2, bar_y_start - total_height,
            arcade.color.DARK_GRAY
        )
        
        # 血条前景
        if entity.max_hp > 0:
            hp_ratio = min(entity.hp / entity.max_hp, 1.0)
            hp_width = entity_bar_width * hp_ratio
            left = entity_bar_x - hp_width / 2
            right = entity_bar_x + hp_width / 2
            if left <= right:
                arcade.draw_lrbt_rectangle_filled(
                    left, right,
                    bar_y_start - total_height * 2, bar_y_start - total_height,
                    arcade.color.GREEN
                )
        
        # 血条边框
        arcade.draw_lrbt_rectangle_outline(
            entity_bar_x - entity_bar_width / 2, entity_bar_x + entity_bar_width / 2,
            bar_y_start - total_height * 2, bar_y_start - total_height,
            arcade.color.BLACK, 2
        )
        
        # 血条文字
        control_marker = "★" if entity.control_type.value == "player" else "●"
        self.draw_text(
            f"{control_marker}{entity.name}: {int(entity.hp)}/{entity.max_hp}",
            entity_bar_x, bar_y_start - total_height * 1.5,
            arcade.color.WHITE, self.text_font_size - 2,
            anchor_x="center", anchor_y="center"
        )
        
        # 如果有职业，显示职业名称
        if has_career:
            career_name = entity.career.name
            # 职业名称背景
            career_text_width = len(career_name) * 10
            arcade.draw_lrbt_rectangle_filled(
                entity_bar_x - career_text_width / 2 - 5,
                entity_bar_x + career_text_width / 2 + 5,
                bar_y_start - total_height * 2 - 15,
                bar_y_start - total_height * 2 - 3,
                (255, 255, 200, 200)
            )
            arcade.draw_lrbt_rectangle_outline(
                entity_bar_x - career_text_width / 2 - 5,
                entity_bar_x + career_text_width / 2 + 5,
                bar_y_start - total_height * 2 - 15,
                bar_y_start - total_height * 2 - 3,
                arcade.color.BLACK, 1
            )
            # 职业名称文字
            self.draw_text(
                career_name,
                entity_bar_x, bar_y_start - total_height * 2 - 9,
                arcade.color.DARK_GOLDENROD, self.text_font_size - 4,
                anchor_x="center", anchor_y="center", bold=True
            )
    
    def _draw_ap_display(self, battle: BattleSystem):
        """绘制AP显示"""
        ap_icon_size = S.scale(16)
        ap_y_pos = S.py(30)
        ap_spacing = S.px(25)
        
        current_entity = battle.current_entity
        if current_entity and current_entity.is_alive():
            is_player_side = current_entity in battle.player_team
            
            if is_player_side:
                ap_start_x = S.px(20)
            else:
                ap_start_x = self.window_width - S.px(20)
            
            # 尝试使用图片
            texture = self.ap_16_texture if hasattr(self, 'ap_16_texture') else None
            
            for i in range(current_entity.ap):
                if is_player_side:
                    x_pos = ap_start_x + i * ap_spacing
                else:
                    x_pos = ap_start_x - i * ap_spacing
                
                if texture:
                    arcade.draw_texture_rect(
                        texture,
                        arcade.XYWH(x_pos - ap_icon_size / 2, ap_y_pos - ap_icon_size / 2,
                                    ap_icon_size, ap_icon_size)
                    )
                else:
                    arcade.draw_circle_filled(x_pos, ap_y_pos, S.scale(8), arcade.color.BLUE)
                    arcade.draw_circle_outline(x_pos, ap_y_pos, S.scale(8), arcade.color.WHITE, 2)
    
    def _draw_mp_display(self, battle: BattleSystem):
        """绘制MP显示"""
        mp_y_pos = S.py(60)  # MP显示在AP上方
        
        current_entity = battle.current_entity
        if current_entity and current_entity.is_alive():
            is_player_side = current_entity in battle.player_team
            
            if is_player_side:
                mp_start_x = S.px(20)
            else:
                mp_start_x = self.window_width - S.px(20)
            
            # 绘制MP文本
            if is_player_side:
                text_x = mp_start_x
            else:
                text_x = mp_start_x
            
            # MP颜色：蓝色渐变，表示魔法值
            mp_color = (100, 149, 237)  # 矢车菊蓝
            
            self.draw_text(
                f"MP: {current_entity.mp}/{current_entity.max_mp}",
                text_x, mp_y_pos,
                mp_color, self.text_font_size,
                anchor_x="left" if is_player_side else "right",
                anchor_y="center",
                bold=True
            )
    
    def _draw_deck_info(self, battle: BattleSystem):
        """绘制卡组和弃牌堆数量信息"""
        current_entity = battle.current_entity
        if not current_entity or not current_entity.is_alive():
            return
        
        # 只显示当前行动实体的卡组信息
        deck_info = current_entity.get_deck_info()
        deck_count = deck_info['deck_count']
        discard_count = deck_info['discard_count']
        hand_count = deck_info['hand_count']
        
        # 确定显示位置（左下角）
        info_x = S.px(20)
        info_y = S.py(80)
        
        # 背景框
        box_width = S.px(180)
        box_height = S.py(60)
        arcade.draw_lrbt_rectangle_filled(
            info_x, info_x + box_width,
            info_y, info_y + box_height,
            (255, 255, 255, 200)
        )
        arcade.draw_lrbt_rectangle_outline(
            info_x, info_x + box_width,
            info_y, info_y + box_height,
            arcade.color.BLACK, 2
        )
        
        # 标题
        self.draw_text(
            f"{current_entity.name} 卡牌信息",
            info_x + box_width / 2, info_y + box_height - S.py(12),
            arcade.color.BLACK, self.text_font_size,
            anchor_x="center", anchor_y="center", bold=True
        )
        
        # 卡组数量
        self.draw_text(
            f"卡组: {deck_count}",
            info_x + S.px(10), info_y + S.py(35),
            arcade.color.DARK_BLUE, self.text_font_size,
            anchor_x="left", anchor_y="center"
        )
        
        # 弃牌堆数量
        self.draw_text(
            f"弃牌堆: {discard_count}",
            info_x + S.px(10), info_y + S.py(18),
            arcade.color.DARK_RED, self.text_font_size,
            anchor_x="left", anchor_y="center"
        )
    
    def draw_battle_log(self, battle: BattleSystem):
        """绘制战斗日志"""
        log_width = S.px(450)
        log_height = S.py(220)
        log_x = S.px(20)
        log_y = self.window_height - log_height - S.py(200)
        
        # 日志背景
        arcade.draw_lrbt_rectangle_filled(
            log_x, log_x + log_width, log_y, log_y + log_height,
            (255, 255, 255, 230)
        )
        arcade.draw_lrbt_rectangle_outline(
            log_x, log_x + log_width, log_y, log_y + log_height,
            arcade.color.BLACK, 2
        )
        
        # 日志标题
        self.draw_text(
            "战斗日志",
            log_x + log_width / 2, log_y + log_height - S.py(20),
            arcade.color.BLACK, self.text_font_size,
            anchor_x="center", anchor_y="center", bold=True
        )
        
        # 日志内容
        log_entries = battle.battle_log.get_last_entries(10)
        if log_entries:
            y_offset = log_y + log_height - S.py(40)
            line_height = S.py(15)
            
            # 定义颜色映射
            color_map = {
                "critical_success": (0, 100, 200),      # 大成功 - 深蓝色
                "success": (0, 180, 0),                 # 成功 - 亮绿色
                "partial_success": (200, 200, 0),       # 半成功 - 黄色
                "failure": (220, 140, 0),               # 失败 - 橙色
                "critical_failure": (220, 0, 0),        # 大失败 - 红色
                "normal": (50, 50, 50)                  # 普通 - 深灰色（更清晰）
            }
            
            for entry in reversed(log_entries):
                if y_offset < log_y + 10:
                    break
                
                message, level, color_key = entry
                
                # 确定颜色
                if message.startswith("==="):
                    color = arcade.color.DARK_BLUE
                    bold = True
                else:
                    color = color_map.get(color_key, arcade.color.BLACK)
                    bold = False
                
                self.draw_text(
                    message, log_x + S.px(8), y_offset,
                    color, self.text_font_size,
                    anchor_x="left", anchor_y="top", bold=bold
                )
                y_offset -= line_height
    
    def draw_entity_info(self, hovered_entity: Entity, battle: BattleSystem):
        """绘制悬停实体的信息"""
        if not hovered_entity:
            return
        
        entity = hovered_entity
        is_player_side = entity in battle.player_team
        
        if is_player_side:
            info_x = S.px(20)
            info_y = self.window_height - S.py(300)
        else:
            info_x = self.window_width - S.px(320)
            info_y = self.window_height - S.py(300)
        
        info_width = S.px(300)
        # 根据是否有职业调整高度
        has_career = hasattr(entity, 'career') and entity.career is not None
        info_height = S.py(200) if has_career else S.py(180)
        
        # 绘制背景
        arcade.draw_lrbt_rectangle_filled(
            info_x, info_x + info_width, info_y, info_y + info_height,
            (255, 255, 255, 240)
        )
        arcade.draw_lrbt_rectangle_outline(
            info_x, info_x + info_width, info_y, info_y + info_height,
            arcade.color.BLACK, 2
        )
        
        # 绘制实体信息
        control_type_text = "玩家控制" if entity.control_type.value == "player" else "AI控制"
        self.draw_text(
            f"{entity.name} ({control_type_text})",
            info_x + info_width / 2, info_y + info_height - S.py(25),
            arcade.color.BLACK, self.title_font_size,
            anchor_x="center", anchor_y="center", bold=True
        )
        
        hp_ratio = entity.hp / entity.max_hp if entity.max_hp > 0 else 0
        hp_color = arcade.color.GREEN if hp_ratio > 0.5 else (arcade.color.ORANGE if hp_ratio > 0.25 else arcade.color.RED)
        
        self.draw_text(
            f"HP: {entity.hp}/{entity.max_hp}",
            info_x + S.px(10), info_y + info_height - S.py(60),
            hp_color, self.text_font_size,
            anchor_x="left", anchor_y="center", bold=True
        )
        
        self.draw_text(
            f"AP: {entity.ap}/{entity.max_ap}",
            info_x + S.px(10), info_y + info_height - S.py(90),
            arcade.color.BLUE, self.text_font_size,
            anchor_x="left", anchor_y="center", bold=True
        )
        
        self.draw_text(
            f"MD: {entity.md}/{entity.max_md}",
            info_x + S.px(10), info_y + info_height - S.py(120),
            arcade.color.ORANGE, self.text_font_size,
            anchor_x="left", anchor_y="center", bold=True
        )
        
        self.draw_text(
            f"格挡: {entity.block}",
            info_x + S.px(10), info_y + info_height - S.py(150),
            arcade.color.GRAY, self.text_font_size,
            anchor_x="left", anchor_y="center"
        )
        
        self.draw_text(
            f"位置: {entity.position}",
            info_x + S.px(10), info_y + info_height - S.py(180),
            arcade.color.DARK_GRAY, self.text_font_size,
            anchor_x="left", anchor_y="center"
        )
        
        # 如果有职业，显示职业信息
        if has_career:
            career_name = entity.career.name
            career_desc = entity.career.description[:30] + "..." if len(entity.career.description) > 30 else entity.career.description
            
            # 职业信息背景
            career_box_y = info_y + info_height - S.py(210)
            arcade.draw_lrbt_rectangle_filled(
                info_x + S.px(5), info_x + info_width - S.px(5),
                career_box_y - S.py(35), career_box_y - S.py(5),
                (255, 255, 200, 150)
            )
            arcade.draw_lrbt_rectangle_outline(
                info_x + S.px(5), info_x + info_width - S.px(5),
                career_box_y - S.py(35), career_box_y - S.py(5),
                arcade.color.DARK_GOLDENROD, 1
            )
            
            # 职业名称
            self.draw_text(
                f"职业: {career_name}",
                info_x + S.px(10), career_box_y - S.py(15),
                arcade.color.DARK_GOLDENROD, self.text_font_size - 2,
                anchor_x="left", anchor_y="center", bold=True
            )
            
            # 职业描述
            self.draw_text(
                career_desc,
                info_x + S.px(10), career_box_y - S.py(30),
                arcade.color.BROWN, max(1, self.text_font_size - 1),
                anchor_x="left", anchor_y="center"
            )
        
        # 绘制装备信息
        if hasattr(entity, 'equipment_manager'):
            from equipment_manager import EquipmentSlot
            equip_mgr = entity.equipment_manager
            weapon = equip_mgr.get_equipped_item(EquipmentSlot.WEAPON)
            armor = equip_mgr.get_equipped_item(EquipmentSlot.BODY)
            
            # 根据是否有职业调整装备信息的Y坐标
            equipment_y = info_y + info_height - S.py(210) if has_career else info_y + info_height - S.py(180)
            
            if weapon:
                self.draw_text(
                    f"武器: {weapon.name}",
                    info_x + S.px(10), equipment_y,
                    arcade.color.ORANGE, self.text_font_size,
                    anchor_x="left", anchor_y="center"
                )
                equipment_y -= S.py(20)
            
            if armor:
                self.draw_text(
                    f"防具: {armor.name}",
                    info_x + S.px(10), equipment_y,
                    arcade.color.BLUE, self.text_font_size,
                    anchor_x="left", anchor_y="center"
                )
        
        # 绘制Buff图标
        if entity.buffs:
            buff_start_y = info_y + S.py(10)
            buff_icon_size = S.scale(24)
            buff_spacing = S.px(30)
            
            for i, (buff_key, buff) in enumerate(entity.buffs.items()):
                buff_x = info_x + S.px(10) + i * buff_spacing
                
                # 绘制AP图标作为buff图标（暂时使用ap_16.png）
                if self.ap_16_texture:
                    arcade.draw_texture_rect(
                        self.ap_16_texture,
                        arcade.XYWH(
                            buff_x,
                            buff_start_y,
                            buff_icon_size,
                            buff_icon_size
                        )
                    )
                else:
                    # 如果没有纹理，绘制圆形
                    arcade.draw_circle_filled(
                        buff_x + buff_icon_size / 2,
                        buff_start_y + buff_icon_size / 2,
                        buff_icon_size / 2,
                        arcade.color.PURPLE
                    )
                
                # 显示层数
                self.draw_text(
                    str(buff.stacks),
                    buff_x + buff_icon_size / 2,
                    buff_start_y + buff_icon_size / 2,
                    arcade.color.WHITE,
                    S.font(10),
                    anchor_x="center",
                    anchor_y="center",
                    bold=True
                )
    
    def draw_battle_end_message(self, battle: BattleSystem):
        """绘制战斗结束消息"""
        overlay_color = (0, 0, 0, 150)
        arcade.draw_rect_filled(
            arcade.XYWH(0, 0, self.window_width, self.window_height),
            overlay_color
        )
        
        winner = battle.winner[0].name if battle.winner else "未知"
        message = f"{winner} 获胜！"
        
        self.draw_text(
            message,
            self.window_width / 2, self.window_height / 2 + S.py(50),
            arcade.color.GOLD, S.font(36),
            anchor_x="center", anchor_y="center", bold=True
        )
        
        self.draw_text(
            "按 ESC 退出",
            self.window_width / 2, self.window_height / 2 - S.py(50),
            arcade.color.WHITE, self.normal_font_size,
            anchor_x="center", anchor_y="center"
        )

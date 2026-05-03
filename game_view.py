"""
Arcade 游戏视图模块
负责所有UI渲染和用户交互
（已重构为模块化架构）
"""
import arcade
from typing import List, Optional, Dict
from models import Entity, Card
from battle_system import BattleSystem
from config import CONSTANTS
from tile_map import TileMap
from ui_renderers import UIRenderer
from card_display import CardDisplay
from input_handlers import InputHandler


class CardView(arcade.View):
    """卡牌战斗游戏主视图（协调各个UI模块）"""
    
    def __init__(self, battle: BattleSystem):
        super().__init__()
        
        self.battle = battle
        # 获取真实屏幕分辨率
        screen_width, screen_height = arcade.get_display_size()
        self.window_width = screen_width if screen_width else CONSTANTS.WINDOW_WIDTH
        self.window_height = screen_height if screen_height else CONSTANTS.WINDOW_HEIGHT
        
        # 瓦片地图相关
        self.tile_map = TileMap(width=20, height=15)
        self.player_position = (2, 7)  # 玩家初始位置
        self.enemy_position = (17, 7)  # 敌人初始位置
        
        # 计算地图偏移量，使地图居中
        map_pixel_width = self.tile_map.width * self.tile_map.tile_size
        map_pixel_height = self.tile_map.height * self.tile_map.tile_size
        self.map_offset_x = (self.window_width - map_pixel_width) / 2
        self.map_offset_y = (self.window_height - map_pixel_height) / 2
        
        # 实体位置映射
        self.entity_positions: Dict[Entity, tuple] = {}
        
        # 初始化UI模块
        self.ui_renderer = UIRenderer(self.window_width, self.window_height)
        self.card_display = CardDisplay(self.ui_renderer)
        self.input_handler = InputHandler(self.battle, self.tile_map, self.card_display)
    

    
    def on_draw(self):
        """绘制游戏画面"""
        self.clear()
        
        # 定期清理过期的Text对象（防止内存泄漏）
        self.ui_renderer.cleanup_text_cache()
        
        # 绘制瓦片地图
        self.ui_renderer.draw_tile_map(
            self.tile_map, self.map_offset_x, self.map_offset_y,
            self.battle, self.entity_positions
        )
        
        # 绘制UI背景
        self._draw_ui_background()

        # 绘制战斗信息
        self.ui_renderer.draw_battle_info(self.battle)

        # 绘制战斗日志
        self.ui_renderer.draw_battle_log(self.battle)
        
        # 绘制手牌（根据当前行动的实体）
        self.card_display.draw_hand(self.battle)
        
        # 绘制悬停实体信息
        if self.input_handler.hovered_entity:
            self.ui_renderer.draw_entity_info(self.input_handler.hovered_entity, self.battle)
        
        # 绘制提示
        if self.battle.battle_finished:
            self.ui_renderer.draw_battle_end_message(self.battle)
    
    def _draw_ui_background(self):
        """绘制UI背景"""
        # 不再绘制遮挡的顶部和底部背景，让UI更清晰
        # 如果需要背景，可以使用淡色
        pass
    

    


    
    def on_mouse_motion(self, x, y, dx, dy):
        """鼠标移动事件"""
        self.input_handler.on_mouse_motion(
            x, y, dx, dy,
            self.map_offset_x, self.map_offset_y,
            self.entity_positions
        )
        
        # 如果正在拖动，更新拖动状态
        if self.card_display.is_dragging():
            self.card_display.update_drag(x, y)
    
    def on_mouse_press(self, x, y, button, modifiers):
        """鼠标点击事件"""
        self.input_handler.on_mouse_press(
            x, y, button, modifiers,
            self.map_offset_x, self.map_offset_y
        )
    
    def on_mouse_release(self, x, y, button, modifiers):
        """鼠标释放事件（用于拖动）"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            # 如果正在拖动，处理拖动结束
            if self.card_display.is_dragging():
                self.input_handler.on_mouse_press(
                    x, y, button, modifiers,
                    self.map_offset_x, self.map_offset_y
                )
                self.card_display.clear_drag()
    
    def on_key_press(self, key, modifiers):
        """键盘按键事件"""
        should_close = self.input_handler.on_key_press(key, modifiers)
        if should_close:
            self.window.close()
    
    def on_update(self, delta_time: float):
        """每帧更新（用于AI逻辑）"""
        # 更新AI出牌逻辑
        self.battle.update_ai()
        
        # 更新卡牌动画
        self.card_display.update_animations()
    


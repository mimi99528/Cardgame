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
from inventory_renderer import InventoryRenderer
from equipment_renderer import EquipmentRenderer


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
        self.tile_map.setup_cameras(self.window_width, self.window_height)  # 初始化相机
        self.player_position = (2, 7)  # 玩家初始位置
        self.enemy_position = (17, 7)  # 敌人初始位置
        
        # 计算地图偏移量，使地图居中（不再需要，改用相机）
        map_pixel_width = self.tile_map.width * self.tile_map.tile_size
        map_pixel_height = self.tile_map.height * self.tile_map.tile_size
        self.map_offset_x = 0  # 不再使用固定偏移
        self.map_offset_y = 0
        
        # 实体位置映射
        self.entity_positions: Dict[Entity, tuple] = {}
        
        # 初始化UI模块
        self.ui_renderer = UIRenderer(self.window_width, self.window_height)
        self.card_display = CardDisplay(self.ui_renderer)
        self.inventory_renderer = InventoryRenderer(self.window_width, self.window_height)
        self.equipment_renderer = EquipmentRenderer(self.window_width, self.window_height)
        self.input_handler = InputHandler(
            self.battle, 
            self.tile_map, 
            self.card_display, 
            self.inventory_renderer,
            self.equipment_renderer
        )
        
        # 将CardView引用设置到BattleSystem中，以便在回合开始时清除拖动状态
        self.battle.card_view = self
        
        # 将tile_map传递给battle系统
        self.battle.tile_map = self.tile_map
    

    
    def on_draw(self):
        """绘制游戏画面"""
        self.clear()
        
        # 定期清理过期的Text对象（防止内存泄漏）
        self.ui_renderer.cleanup_text_cache()
        
        # 激活地图相机
        if self.tile_map.camera:
            self.tile_map.camera.use()
        
        # 绘制瓦片地图（使用相机系统，不再需要偏移量）
        self.ui_renderer.draw_tile_map(
            self.tile_map, self.map_offset_x, self.map_offset_y,
            self.battle, self.entity_positions
        )
        
        # 切换到GUI相机（用于UI元素）
        if self.tile_map.gui_camera:
            self.tile_map.gui_camera.use()
        
        # 绘制UI背景
        self._draw_ui_background()

        # 绘制战斗信息
        self.ui_renderer.draw_battle_info(self.battle)

        # 绘制战斗日志
        self.ui_renderer.draw_battle_log(self.battle)
        
        # 绘制手牌（根据当前行动的实体）
        self.card_display.draw_hand(self.battle)
        
        # 绘制背包界面（如果在显示状态）
        self.inventory_renderer.draw()
        
        # 绘制装备界面（如果在显示状态）
        self.equipment_renderer.draw()
        
        # 绘制悬停实体信息
        if self.input_handler.hovered_entity:
            self.ui_renderer.draw_entity_info(self.input_handler.hovered_entity, self.battle)
        
        # 绘制提示
        if self.battle.battle_finished:
            self.ui_renderer.draw_battle_end_message(self.battle)
            # 绘制重新开始按钮
            self._draw_restart_button()
        
        # 重置相机（确保下次绘制正确）
        arcade.Camera2D().use()  # 使用默认相机
    
    def _draw_ui_background(self):
        """绘制UI背景"""
        # 不再绘制遮挡的顶部和底部背景，让UI更清晰
        # 如果需要背景，可以使用淡色
        pass
    
    def _draw_restart_button(self):
        """绘制重新开始按钮"""
        button_width = 200
        button_height = 50
        button_x = self.window_width // 2 - button_width // 2
        button_y = self.window_height // 2 - 100
        
        # 绘制按钮背景
        arcade.draw_rectangle_filled(
            button_x + button_width // 2,
            button_y + button_height // 2,
            button_width,
            button_height,
            arcade.color.DARK_GREEN
        )
        
        # 绘制按钮边框
        arcade.draw_rectangle_outline(
            button_x + button_width // 2,
            button_y + button_height // 2,
            button_width,
            button_height,
            arcade.color.WHITE,
            border_width=3
        )
        
        # 绘制按钮文字
        arcade.draw_text(
            "再来一局",
            button_x + button_width // 2,
            button_y + button_height // 2,
            arcade.color.WHITE,
            24,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
    
    def _handle_inventory_item_use(self, x: float, y: float):
        """处理背包物品使用（右键点击）"""
        if not self.inventory_renderer.current_inventory:
            return
        
        # 获取当前行动的实体
        current_entity = self.battle.current_entity
        if not current_entity:
            # 警告：没有活动实体
            return
        
        # 检查是否点击了物品
        clicked_item = self.inventory_renderer.get_item_at_position(x, y)
        if clicked_item:
            success, message = self.inventory_renderer.current_inventory.use_item(
                clicked_item, 
                user_entity=current_entity,
                battle_log=self.battle.battle_log
            )
            
            if success:
                # 记录到战斗日志
                self.battle.battle_log.add(message, level=0)
    

    


    
    def on_mouse_motion(self, x, y, dx, dy):
        """鼠标移动事件（仅用于悬停检测）"""
        # 如果背包打开，只更新背包悬停，不处理其他悬停
        if self.inventory_renderer.is_visible():
            self.inventory_renderer.update_hover(x, y)
            return
        
        # 如果装备界面打开，需要同时更新装备界面和输入处理器
        if self.equipment_renderer.is_visible():
            # 先让input_handler处理拖动更新
            self.input_handler.on_mouse_motion(
                x, y, dx, dy,
                self.map_offset_x, self.map_offset_y,
                self.entity_positions,
                self.window_width, self.window_height
            )
            return
        
        self.input_handler.on_mouse_motion(
            x, y, dx, dy,
            self.map_offset_x, self.map_offset_y,
            self.entity_positions,
            self.window_width, self.window_height
        )
        
        # 更新背包悬停状态
        self.inventory_renderer.update_hover(x, y)
    
    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        """
        鼠标拖动事件（用于移动地图和卡牌拖动）
        
        Args:
            x, y: 当前鼠标位置
            dx, dy: 鼠标移动增量
            buttons: 按下的鼠标按钮
            modifiers: 键盘修饰键
        """
        # 如果装备界面打开，处理装备拖动
        if self.equipment_renderer.is_visible():
            # 如果正在拖动装备，更新拖动位置
            if self.equipment_renderer.dragged_item and buttons & arcade.MOUSE_BUTTON_LEFT:
                self.input_handler.on_mouse_motion(
                    x, y, dx, dy,
                    self.map_offset_x, self.map_offset_y,
                    self.entity_positions,
                    self.window_width, self.window_height
                )
            return
        
        # 如果背包界面打开，禁止拖动操作
        if self.inventory_renderer.is_visible():
            return
        
        # 如果正在拖动卡牌（左键），更新拖动位置
        if buttons & arcade.MOUSE_BUTTON_LEFT and self.card_display.is_dragging():
            self.card_display.update_drag(x, y)
        # 否则，如果中键或右键拖动，移动地图
        elif buttons & (arcade.MOUSE_BUTTON_MIDDLE | arcade.MOUSE_BUTTON_RIGHT):
            self.tile_map.on_mouse_drag(x, y, dx, dy, self.window_width, self.window_height)
    
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """
        鼠标滚轮事件（用于缩放地图）
        
        Args:
            x, y: 鼠标位置
            scroll_x: 水平滚动量
            scroll_y: 垂直滚动量（正数=放大，负数=缩小）
        """
        # 如果背包或装备界面打开，禁止缩放
        if self.inventory_renderer.is_visible() or self.equipment_renderer.is_visible():
            return
        
        self.tile_map.on_mouse_scroll(scroll_x, scroll_y)
    
    def on_mouse_press(self, x, y, button, modifiers):
        """鼠标点击事件"""
        # 如果战斗结束，检查是否点击了重新开始按钮
        if self.battle.battle_finished and button == arcade.MOUSE_BUTTON_LEFT:
            if self._check_restart_button_click(x, y):
                self._restart_game()
                return
        
        # 如果背包打开，处理背包内的点击
        if self.inventory_renderer.is_visible():
            # 右键点击使用物品
            if button == arcade.MOUSE_BUTTON_RIGHT:
                self._handle_inventory_item_use(x, y)
            return
        
        self.input_handler.on_mouse_press(
            x, y, button, modifiers,
            self.map_offset_x, self.map_offset_y,
            self.window_width, self.window_height
        )
    
    def on_mouse_release(self, x, y, button, modifiers):
        """鼠标释放事件（用于拖动）"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            # 如果正在拖动卡牌，处理拖动结束
            if self.card_display.is_dragging():
                self.input_handler.on_mouse_release(
                    x, y, button, modifiers,
                    self.map_offset_x, self.map_offset_y,
                    self.window_width, self.window_height
                )
                self.card_display.clear_drag()
            else:
                # 处理装备拖动等其他拖动操作
                self.input_handler.on_mouse_release(
                    x, y, button, modifiers,
                    self.map_offset_x, self.map_offset_y,
                    self.window_width, self.window_height
                )
    
    def on_key_press(self, key, modifiers):
        """键盘按键事件"""
        should_close = self.input_handler.on_key_press(key, modifiers)
        if should_close:
            self.window.close()
    
    def on_update(self, delta_time: float):
        """每帧更新（用于AI逻辑）"""
        # 如果背包打开，暂停游戏更新
        if self.inventory_renderer.is_visible():
            return
        
        # 更新AI出牌逻辑
        self.battle.update_ai()
        
        # 更新卡牌动画
        self.card_display.update_animations()
    
    def _check_restart_button_click(self, x: float, y: float) -> bool:
        """检查是否点击了重新开始按钮"""
        button_width = 200
        button_height = 50
        button_x = self.window_width // 2 - button_width // 2
        button_y = self.window_height // 2 - 100
        
        return (button_x <= x <= button_x + button_width and
                button_y <= y <= button_y + button_height)
    
    def _restart_game(self):
        """重新开始游戏 - 返回角色创建界面"""
        from character_creation import CharacterCreationView
        from main import CardGame
        
        # 获取主窗口引用
        window = self.window
        
        # 创建新的角色创建视图
        character_creation_view = CharacterCreationView(window.on_character_created)
        window.show_view(character_creation_view)
    


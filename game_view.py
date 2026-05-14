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
from narrative_renderer import NarrativeSceneRenderer
from narrative_system import NarrativeNodeManager, NarrativeResultEngine
from ui_scale import S, update_scale


class CardView(arcade.View):
    """卡牌战斗游戏主视图（协调各个UI模块）"""
    
    def __init__(self, battle: BattleSystem):
        super().__init__()
        
        self.battle = battle
        # 使用配置中自动检测的窗口尺寸
        self.window_width = CONSTANTS.WINDOW_WIDTH
        self.window_height = CONSTANTS.WINDOW_HEIGHT
        
        # 调试 overlay（按 F3 切换）
        self.debug_overlay_visible: bool = False
        
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
        self.narrative_renderer = NarrativeSceneRenderer(self.window_width, self.window_height)
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
        
        # 叙事场景相关
        self.narrative_node_manager = NarrativeNodeManager()
        self.current_narrative_node = None
        self.narrative_mode = False  # 是否处于叙事模式
        
        # 加载叙事节点
        try:
            self.narrative_node_manager.load_from_file("narrative_nodes.json")
            print(f"✓ 已加载 {len(self.narrative_node_manager.get_all_nodes())} 个叙事节点")
        except Exception as e:
            print(f"警告：加载叙事节点失败: {e}")
    
    def on_resize(self, width: int, height: int):
        """窗口尺寸变化时更新内部尺寸并刷新各子模块。"""
        self.window_width = width
        self.window_height = height
        self.ui_renderer.on_resize(width, height)
        self.tile_map.setup_cameras(width, height)
        self.inventory_renderer.window_width = width
        self.inventory_renderer.window_height = height
        self.equipment_renderer.window_width = width
        self.equipment_renderer.window_height = height
        self.equipment_renderer._calculate_panel_position()
        self.narrative_renderer.on_resize(width, height)
    

    
    def on_draw(self):
        """绘制游戏画面"""
        # 调试：记录每次绘制时的视图状态
        print(f"[DEBUG] CardView.on_draw called, current_view type: {type(self.window.current_view)}")
        
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
            # 调试：确认GUI相机状态
            print(f"[DEBUG] GUI camera after use: position={self.tile_map.gui_camera.position}, zoom={self.tile_map.gui_camera.zoom}")
        
        # 【调试】绘制测试框 - 左下角和右下角标记
        # 左下角标记（应该显示在屏幕左下角）
        arcade.draw_circle_filled(50, 50, 20, arcade.color.RED)
        arcade.draw_text("左下角(50,50)", 50, 80, arcade.color.RED, 16, anchor_x="center")
        
        # 右下角标记（应该显示在屏幕右下角）
        arcade.draw_circle_filled(self.window_width - 50, 50, 20, arcade.color.GREEN)
        arcade.draw_text("右下角", self.window_width - 50, 80, arcade.color.GREEN, 16, anchor_x="center")
        
        # 左上角标记
        arcade.draw_circle_filled(50, self.window_height - 50, 20, arcade.color.BLUE)
        arcade.draw_text("左上角", 50, self.window_height - 20, arcade.color.BLUE, 16, anchor_x="center")
        
        # 右上角标记
        arcade.draw_circle_filled(self.window_width - 50, self.window_height - 50, 20, arcade.color.YELLOW)
        arcade.draw_text("右上角", self.window_width - 50, self.window_height - 20, arcade.color.YELLOW, 16, anchor_x="center")
        
        # 绘制UI背景
        self._draw_ui_background()

        # 绘制战斗信息
        self.ui_renderer.draw_battle_info(self.battle)

        # 绘制战斗日志
        self.ui_renderer.draw_battle_log(self.battle)
        
        # 绘制手牌（根据当前行动的实体）
        # 如果在叙事模式下，传递叙事节点以过滤手牌
        self.card_display.draw_hand(
            self.battle,
            narrative_mode=self.narrative_mode,
            current_node=self.current_narrative_node
        )
        
        # 绘制背包界面（如果在显示状态）
        self.inventory_renderer.draw()
        
        # 绘制装备界面（如果在显示状态）
        self.equipment_renderer.draw()
        
        # 绘制叙事场景（如果在叙事模式）
        if self.narrative_mode and self.current_narrative_node:
            self.narrative_renderer.draw()
        
        # 绘制悬停实体信息
        if self.input_handler.hovered_entity:
            self.ui_renderer.draw_entity_info(self.input_handler.hovered_entity, self.battle)
        
        # 绘制提示
        if self.battle.battle_finished:
            self.ui_renderer.draw_battle_end_message(self.battle)
            # 只在玩家失败时绘制重新开始按钮
            if self.battle.player_defeated:
                self._draw_restart_button()
            else:
                # 玩家胜利时，检查是否有生命骰回血需要处理
                if hasattr(self.battle, 'hit_dice_recovery_queue') and self.battle.hit_dice_recovery_queue:
                    # 有生命骰回血需要处理，不显示其他按钮
                    pass
                elif hasattr(self.battle, 'dropped_cards_for_selection') and self.battle.dropped_cards_for_selection:
                    # 有掉落卡牌，显示战利品选择UI
                    self._show_loot_selection()
                # 如果已经显示过卡组编辑，不再显示结束战斗按钮（直接进入叙事）
                elif not getattr(self, '_deck_edit_shown', False):
                    self._draw_end_battle_button()
        
        # 调试 overlay（按 F3 切换，便于验证 4K/高 DPI 缩放是否正确）
        if self.debug_overlay_visible:
            self._draw_debug_overlay()
    
    def _draw_ui_background(self):
        """绘制UI背景"""
        # 不再绘制遮挡的顶部和底部背景，让UI更清晰
        # 如果需要背景，可以使用淡色
        pass
    
    def _draw_debug_overlay(self):
        """调试 overlay：显示当前窗口尺寸和 UIScale 缩放系数（按 F3 切换）。"""
        lines = [
            f"窗口: {self.window_width} × {self.window_height} px",
            f"缩放: sx={S.sx:.3f}  sy={S.sy:.3f}  s={S.s:.3f}",
            f"设计分辨率: 1920 × 1080",
            f"字体示例: font(16) = {S.font(16)}  font(24) = {S.font(24)}",
        ]
        bg_w, bg_h = S.px(400), S.py(100)
        bg_x, bg_y = S.px(10), self.window_height - bg_h - S.py(10)
        arcade.draw_lrbt_rectangle_filled(
            bg_x, bg_x + bg_w, bg_y, bg_y + bg_h,
            (0, 0, 0, 180)
        )
        arcade.draw_lrbt_rectangle_outline(
            bg_x, bg_x + bg_w, bg_y, bg_y + bg_h,
            arcade.color.YELLOW, 2
        )
        for i, line in enumerate(lines):
            arcade.draw_text(
                line,
                bg_x + S.px(8),
                bg_y + bg_h - S.py(16) - i * S.py(20),
                arcade.color.YELLOW,
                S.font(11),
                anchor_x="left", anchor_y="center"
            )
    
    def _draw_restart_button(self):
        """绘制重新开始按钮"""
        button_width = S.px(200)
        button_height = S.py(50)
        button_x = self.window_width // 2 - button_width // 2
        button_y = self.window_height // 2 - S.py(200)
        left = button_x
        right = button_x + button_width
        bottom = button_y
        top = button_y + button_height
        
        # 绘制按钮背景
        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top,
            arcade.color.DARK_GREEN
        )
        
        # 绘制按钮边框
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top,
            arcade.color.WHITE,
            border_width=3
        )
        
        # 绘制按钮文字
        arcade.draw_text(
            "再来一局",
            button_x + button_width // 2,
            button_y + button_height // 2,
            arcade.color.WHITE,
            S.font(24),
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
        # 如果处于叙事模式，处理叙事场景的点击
        if self.narrative_mode and self.current_narrative_node:
            if button == arcade.MOUSE_BUTTON_LEFT:
                # 检查是否点击了选项
                action = self.narrative_renderer.handle_option_click(x, y)
                if action:
                    self._handle_narrative_action(action)
                    return
                
                # 检查是否点击了确定按钮
                if self.narrative_renderer.handle_confirm_click(x, y):
                    self._handle_narrative_confirm()
                    return
            return
        
        # 如果战斗结束，检查是否点击了重新开始按钮或结束战斗按钮
        if self.battle.battle_finished and button == arcade.MOUSE_BUTTON_LEFT:
            if self.battle.player_defeated:
                # 玩家失败，检查重新开始按钮
                if self._check_restart_button_click(x, y):
                    self._restart_game()
                    return
            else:
                # 玩家胜利，检查是否有生命骰回血需要处理
                if hasattr(self.battle, 'hit_dice_recovery_queue') and self.battle.hit_dice_recovery_queue:
                    # 显示生命骰回血UI
                    self._show_hit_dice_recovery()
                    return
                
                # 检查结束战斗按钮
                # 注意：即使有掉落卡牌，如果已经选择过了，也应该能点击结束战斗
                if self._check_end_battle_button_click(x, y):
                    print("[DEBUG] 点击了结束战斗按钮")
                    self._end_battle_and_start_narrative()
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
            # 如果处于叙事模式，检查是否拖动了卡牌到场景视图
            if self.narrative_mode and self.current_narrative_node:
                if self.card_display.is_dragging():
                    dragged_card = self.card_display.dragged_card
                    if dragged_card:
                        self._handle_card_drop_on_narrative(dragged_card)
                    self.card_display.clear_drag()
                    return
            
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
        # F3 切换调试 overlay（显示窗口尺寸和缩放系数）
        if key == arcade.key.F3:
            self.debug_overlay_visible = not self.debug_overlay_visible
            return
        
        # Shift+M: 切换到地图场景
        if key == arcade.key.M and (modifiers & arcade.key.MOD_SHIFT):
            self._switch_to_map_scene()
            return
        
        # Shift+F3: Debug功能 - 跳过战斗直接胜利以测试叙事场景
        if key == arcade.key.F1 and (modifiers & arcade.key.MOD_SHIFT):
            self._debug_skip_battle_to_victory()
            return
        
        # Shift+F2: Debug功能 - 跳过战斗直接进入领取奖励环节
        if key == arcade.key.F2 and (modifiers & arcade.key.MOD_SHIFT):
            self._debug_skip_battle_to_loot()
            return
        
        should_close = self.input_handler.on_key_press(key, modifiers)
        if should_close:
            self.window.close()
    
    def _switch_to_map_scene(self):
        """切换到地图场景"""
        print("\n[DEBUG] Shift+M pressed - Switching to map scene")
        from scene_manager import MapSceneView
        map_scene = MapSceneView(self.battle, window=self.window)
        self.window.show_view(map_scene)
    
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
        button_width = S.px(200)
        button_height = S.py(50)
        button_x = self.window_width // 2 - button_width // 2
        button_y = self.window_height // 2 - S.py(200)
        
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
    
    def _debug_skip_battle_to_victory(self):
        """Debug功能：跳过战斗直接胜利并切换到叙事场景"""
        print("\n[DEBUG] Shift+F3 pressed - Skipping battle to victory")
            
        # 标记战斗结束，玩家胜利
        self.battle.battle_finished = True
        self.battle.winner = self.battle.player_team
        self.battle.player_defeated = False
        self.battle.battle_log.add("\n[DEBUG] 战斗已跳过，玩家胜利！")
            
        # 直接切换到叙事场景（跳过点击按钮的步骤）
        print("[DEBUG] 直接切换到叙事场景")
        from scene_manager import NarrativeSceneView
        narrative_scene = NarrativeSceneView(self.battle, "gate_guard_001")
        self.window.show_view(narrative_scene)
    
    def _debug_skip_battle_to_loot(self):
        """Debug功能：跳过战斗直接进入领取奖励环节"""
        print("\n[DEBUG] Shift+F2 pressed - Skipping battle to loot selection")
        
        # 标记战斗结束，玩家胜利
        self.battle.battle_finished = True
        self.battle.winner = self.battle.player_team
        self.battle.player_defeated = False
        self.battle.battle_log.add("\n[DEBUG] 战斗已跳过，进入奖励选择！")
        
        # 将所有敌人设为死亡状态，以便生成掉落
        print("[DEBUG] 将所有敌人设为死亡状态")
        for enemy in self.battle.enemy_team:
            if enemy.is_alive():
                enemy.current_health = 0
                print(f"  - {enemy.name} 已设为死亡")
        
        # 生成战利品
        print("[DEBUG] 生成战利品")
        self.battle._generate_battle_loot()
        
        # 检查是否生成了掉落卡牌
        if hasattr(self.battle, 'dropped_cards_for_selection') and self.battle.dropped_cards_for_selection:
            print(f"[DEBUG] 成功生成 {len(self.battle.dropped_cards_for_selection)} 张掉落卡牌")
        else:
            print("[DEBUG] 警告：没有生成掉落卡牌，创建测试卡牌")
            # 如果没生成，手动创建测试卡牌
            from card_database import create_card_database
            from models import Rarity
            import random
            
            test_cards = []
            cards_db = create_card_database()
            all_cards = list(cards_db.values())
            
            if len(all_cards) >= 3:
                # 尝试选择不同稀有度的卡牌
                rarities = [Rarity.COMMON, Rarity.UNCOMMON, Rarity.RARE]
                for rarity in rarities:
                    cards_of_rarity = [c for c in all_cards if c.rarity == rarity]
                    if cards_of_rarity:
                        test_cards.append(random.choice(cards_of_rarity))
                
                # 如果不足3张，用随机卡牌补充
                while len(test_cards) < 3 and all_cards:
                    card = random.choice(all_cards)
                    if card not in test_cards:
                        test_cards.append(card)
            
            self.battle.dropped_cards_for_selection = test_cards[:3]
            print(f"[DEBUG] 创建了 {len(test_cards[:3])} 张测试卡牌")
        
        # 显示战利品选择UI
        print("[DEBUG] 显示战利品选择UI")
        self._show_loot_selection()
    
    def _start_narrative_scene(self, node_id: str):
        """
        启动叙事场景
        
        Args:
            node_id: 叙事节点ID
        """
        node = self.narrative_node_manager.get_node(node_id)
        if not node:
            print(f"警告：未找到叙事节点 {node_id}")
            return
        
        print(f"\n[叙事] 启动场景: {node.title}")
        
        # 设置叙事模式
        self.narrative_mode = True
        self.current_narrative_node = node
        
        # 设置玩家实体到叙事渲染器
        player = self.battle.player
        if player:
            self.narrative_renderer.set_node(node, player)
        
        # 清除拖动状态
        self.card_display.clear_drag()
        
        print(f"[叙事] 场景 '{node.title}' 已启动，可用动作数: {len(node.actions)}")
    
    def _handle_narrative_action(self, action):
        """
        处理叙事动作选择
        
        Args:
            action: 选中的叙事动作
        """
        print(f"\n[叙事] 选择动作: {action.name}")
        
        # 设置选中的动作
        self.narrative_renderer.selected_action = action
        
        # 获取玩家实体
        player = self.battle.player
        if not player:
            print("警告：未找到玩家实体")
            return
        
        # 执行检定
        dice_total, stat_bonus, final_result, outcome = NarrativeResultEngine.perform_check(action, player.stats)
        
        print(f"[叙事] 检定结果: 骰子={dice_total}, 加值={stat_bonus}, 最终={final_result}, 结果={outcome}")
        
        # 生成叙事结果
        result = NarrativeResultEngine.generate_result(
            self.current_narrative_node,
            action,
            outcome,
            player.stats
        )
        
        if result:
            print(f"[叙事] 结果文本: {result.text[:80]}...")
            self.narrative_renderer.current_result = result
        else:
            print(f"警告：未找到结果 (outcome={outcome})")
    
    def _handle_narrative_confirm(self):
        """处理叙事确定按钮点击"""
        print("\n[叙事] 点击确定按钮")
        
        if not self.narrative_renderer.current_result:
            print("警告：没有当前结果")
            return
        
        # 获取结果等级
        outcome_level = self.narrative_renderer.current_result.outcome_level
        
        # 查找下一节点
        next_node_id = self.current_narrative_node.next_nodes.get(outcome_level)
        
        if next_node_id:
            print(f"[叙事] 跳转到下一节点: {next_node_id}")
            # 切换到下一节点
            self._start_narrative_scene(next_node_id)
        else:
            print(f"[叙事] 叙事结束（无下一节点）")
            # 退出叙事模式
            self._exit_narrative_mode()
    
    def _handle_card_drop_on_narrative(self, card: Card):
        """
        处理卡牌拖放到叙事场景
        
        Args:
            card: 拖放的卡牌
        """
        print(f"\n[叙事] 卡牌拖放: {card.name}")
        
        if not self.current_narrative_node:
            return
        
        # 检查卡牌是否有叙事动作（通过卡牌的 tags 来匹配节点的 required_tags）
        for action in self.current_narrative_node.actions:
            if action.is_hidden and action.name not in self.narrative_renderer.revealed_hidden_actions:
                # 获取卡牌的标签值列表
                card_tag_values = [t.value if hasattr(t, 'value') else str(t) for t in card.tags]
                # 检查卡牌标签是否匹配隐藏动作所需的标签
                if any(req_tag in card_tag_values for req_tag in action.required_tags):
                    self.narrative_renderer.reveal_hidden_action(action.name)
                    print(f"[叙事] 揭示隐藏动作: {action.name}")
                    
                    # 显示提示
                    self.battle.battle_log.add(f"揭示了隐藏选项: {action_name}", level=0)
                    break
    
    def _exit_narrative_mode(self):
        """退出叙事模式"""
        print("\n[叙事] 退出叙事模式")
        self.narrative_mode = False
        self.current_narrative_node = None
        self.narrative_renderer.hide()
    
    def _draw_end_battle_button(self):
        """绘制结束战斗按钮（玩家胜利时显示）"""
        button_width = S.px(200)
        button_height = S.py(50)
        button_x = self.window_width // 2 - button_width // 2
        button_y = self.window_height // 2 - S.py(100)  # 比重试按钮高一些
        left = button_x
        right = button_x + button_width
        bottom = button_y
        top = button_y + button_height
        
        # 绘制按钮背景
        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top,
            arcade.color.DARK_GREEN
        )
        
        # 绘制按钮边框
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top,
            arcade.color.WHITE,
            border_width=3
        )
        
        # 绘制按钮文字
        arcade.draw_text(
            "结束战斗",
            button_x + button_width // 2,
            button_y + button_height // 2,
            arcade.color.WHITE,
            S.font(24),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
    
    def _check_end_battle_button_click(self, x: float, y: float) -> bool:
        """检查是否点击了结束战斗按钮"""
        button_width = S.px(200)
        button_height = S.py(50)
        button_x = self.window_width // 2 - button_width // 2
        button_y = self.window_height // 2 - S.py(100)
        
        return (button_x <= x <= button_x + button_width and
                button_y <= y <= button_y + button_height)
    
    def _show_hit_dice_recovery(self):
        """显示生命骰回血选择UI"""
        print(f"\n>>> 显示生命骰回血UI <<<")
        print(f"需要回血的实体数量: {len(self.battle.hit_dice_recovery_queue)}")
        
        for i, data in enumerate(self.battle.hit_dice_recovery_queue, 1):
            print(f"  {i}. {data['name']}: HP={data['current_hp']}/{data['max_hp']}, "
                  f"生命骰={data['current_hit_dice']}/{data['max_hit_dice']}")
        
        def on_recovery_complete():
            """回血完成回调"""
            print("\n✓ 生命骰回血完成")
            # 清除回血队列
            self.battle.hit_dice_recovery_queue = []
            
            # 回血完成后，直接进入卡组编辑界面
            self._show_deck_edit()
        
        # 导入生命骰回血视图
        from hit_dice_recovery_view import HitDiceRecoveryView
        
        # 保存当前游戏视图引用
        self.window._game_view = self
        
        # 创建并显示生命骰回血视图
        recovery_view = HitDiceRecoveryView(
            self.battle.hit_dice_recovery_queue,
            on_recovery_complete
        )
        self.window.show_view(recovery_view)
    
    def _return_cards_to_deck(self):
        """将手牌和弃牌堆中的卡牌全部放回卡组（排除常驻卡牌和装备卡牌）"""
        player = self.battle.player
        if not player:
            print("[ERROR] 玩家不存在，无法回收卡牌")
            return
        
        print("\n" + "="*60)
        print("[DEBUG] 开始回收卡牌到卡组")
        print("="*60)
        
        print(f"[DEBUG] 回收前状态:")
        print(f"  - 手牌数量: {len(player.hand)}")
        if player.hand:
            print(f"  - 手牌列表: {[c.name for c in player.hand]}")
        else:
            print(f"  - 手牌列表: (空)")
        
        print(f"  - 弃牌堆数量: {len(player.discard_pile)}")
        if player.discard_pile:
            print(f"  - 弃牌堆列表: {[c.name for c in player.discard_pile]}")
        else:
            print(f"  - 弃牌堆列表: (空)")
        
        print(f"  - 当前卡组大小: {len(player.deck)}")
        if player.deck:
            print(f"  - 卡组列表: {[c.name for c in player.deck]}")
        else:
            print(f"  - 卡组列表: (空)")
        
        # 显示装备卡牌信息
        if hasattr(player, 'equipment_cards') and player.equipment_cards:
            print(f"  - 装备卡牌数量: {len(player.equipment_cards)}")
            print(f"  - 装备卡牌列表: {[c.name for c in player.equipment_cards]}")
        else:
            print(f"  - 装备卡牌数量: 0")
        print("="*60)
        
        cards_returned_count = 0
        
        # 将手牌中的卡牌放回卡组（排除常驻卡牌和装备卡牌）
        hand_cards_to_return = []
        for card in player.hand:
            # 检查是否是常驻卡牌
            if hasattr(player, 'permanent_cards') and card in player.permanent_cards:
                print(f"[DEBUG] 跳过常驻卡牌: {card.name}")
                continue
            # 检查是否是装备卡牌
            if hasattr(player, 'equipment_cards') and card in player.equipment_cards:
                print(f"[DEBUG] 跳过装备卡牌: {card.name}")
                continue
            hand_cards_to_return.append(card)
        
        # 从手牌移除并加入卡组
        if hand_cards_to_return:
            print(f"\n[DEBUG] 开始回收手牌 ({len(hand_cards_to_return)} 张):")
            for card in hand_cards_to_return:
                player.hand.remove(card)
                player.deck.append(card)
                cards_returned_count += 1
                print(f"  [✓] 手牌 -> 卡组: {card.name}")
        else:
            print("\n[DEBUG] 手牌中没有可回收的卡牌")
        
        # 将弃牌堆中的卡牌放回卡组
        discard_cards_to_return = list(player.discard_pile)
        if discard_cards_to_return:
            print(f"\n[DEBUG] 开始回收弃牌堆 ({len(discard_cards_to_return)} 张):")
            for card in discard_cards_to_return:
                player.discard_pile.remove(card)
                player.deck.append(card)
                cards_returned_count += 1
                print(f"  [✓] 弃牌堆 -> 卡组: {card.name}")
        else:
            print("\n[DEBUG] 弃牌堆中没有可回收的卡牌")
        
        print("\n" + "="*60)
        print(f"[DEBUG] 卡牌回收完成")
        print(f"[DEBUG] 总共回收: {cards_returned_count} 张卡牌")
        print(f"[DEBUG] 回收后状态:")
        print(f"  - 最终手牌数量: {len(player.hand)}")
        print(f"  - 最终弃牌堆数量: {len(player.discard_pile)}")
        print(f"  - 最终卡组大小: {len(player.deck)}")
        if player.deck:
            print(f"  - 最终卡组列表: {[c.name for c in player.deck]}")
        else:
            print(f"  - 最终卡组列表: (空)")
        print("="*60 + "\n")
    
    def _end_battle_and_start_narrative(self):
        """结束战斗并切换到叙事场景"""
        print("\n" + "#"*60)
        print("[系统] 结束战斗，切换到叙事场景")
        print("#"*60)
        print(f"[DEBUG] 当前窗口: {self.window}")
        print(f"[DEBUG] 当前视图: {self.window.current_view}")
        print(f"[DEBUG] 准备切换到 NarrativeSceneView")
        
        # 标记已经完成所有战后流程（战利品选择 + 卡组编辑）
        self._deck_edit_shown = True
        
        # 再次回收卡牌（编辑完成后手牌可能还有残留）
        print("\n[DEBUG] 编辑完成后再次回收卡牌...")
        self._return_cards_to_deck()
        print("[DEBUG] 第二次回收完成")
        
        # 使用场景管理器切换到叙事场景，传递窗口引用
        from scene_manager import NarrativeSceneView
        narrative_scene = NarrativeSceneView(self.battle, "gate_guard_001", window=self.window)
        print(f"[DEBUG] 已创建 NarrativeSceneView: {narrative_scene}")
        print(f"[DEBUG] NarrativeSceneView.window: {narrative_scene.window}")
        
        # 关键修复：先隐藏当前视图，再显示新视图
        # 这样可以确保Arcade框架正确处理视图切换
        self.window.show_view(narrative_scene)
        
        # 验证切换是否成功
        print(f"[DEBUG] 切换后的当前视图: {self.window.current_view}")
        print(f"[DEBUG] 视图类型: {type(self.window.current_view)}")
        print(f"[DEBUG] 视图是否相同: {self.window.current_view is narrative_scene}")
        print(f"[DEBUG] 已调用 show_view，应该已切换")
    
    def _end_battle_and_start_map(self):
        """结束战斗并切换到地图场景"""
        print("\n" + "#"*60)
        print("[系统] 结束战斗，切换到地图场景")
        print("#"*60)
        
        # 标记已经完成所有战后流程（战利品选择 + 卡组编辑）
        self._deck_edit_shown = True
        
        # 再次回收卡牌（编辑完成后手牌可能还有残留）
        print("\n[DEBUG] 编辑完成后再次回收卡牌...")
        self._return_cards_to_deck()
        print("[DEBUG] 第二次回收完成")
        
        # 使用场景管理器切换到地图场景，传递窗口引用
        from scene_manager import MapSceneView
        map_scene = MapSceneView(self.battle, window=self.window)
        print(f"[DEBUG] 已创建 MapSceneView: {map_scene}")
        
        # 切换到地图场景
        self.window.show_view(map_scene)
        
        # 验证切换是否成功
        print(f"[DEBUG] 切换后的当前视图: {self.window.current_view}")
        print(f"[DEBUG] 视图类型: {type(self.window.current_view)}")
        print(f"[DEBUG] 已切换到地图场景")
    
    def _show_loot_selection(self):
        """显示战利品选择UI"""
        print(f"[DEBUG] _show_loot_selection called")
        print(f"[DEBUG] dropped_cards_for_selection: {self.battle.dropped_cards_for_selection}")
        print(f"[DEBUG] _loot_selection_shown: {getattr(self, '_loot_selection_shown', False)}")
        
        if not hasattr(self.battle, 'dropped_cards_for_selection') or not self.battle.dropped_cards_for_selection:
            print(f"[DEBUG] 没有掉落卡牌，只绘制结束按钮")
            self._draw_end_battle_button()
            return
        
        # 检查是否已经显示了战利品选择UI（防止重复显示）
        if hasattr(self, '_loot_selection_shown') and self._loot_selection_shown:
            # 已经显示过了，只绘制结束战斗按钮
            print(f"[DEBUG] 已经显示过战利品选择，只绘制结束按钮")
            self._draw_end_battle_button()
            return
        
        dropped_cards = self.battle.dropped_cards_for_selection
        
        print(f"\n>>> 显示战利品选择UI <<<")
        print(f"掉落卡牌数量: {len(dropped_cards)}")
        for i, card in enumerate(dropped_cards, 1):
            print(f"  {i}. {card.name} ({['普通', '优秀', '稀有', '传说'][card.rarity.value]})")
        
        def on_selection_complete(selected_card):
            """选择完成回调"""
            # 立即标记已显示过，防止重复显示
            self._loot_selection_shown = True
            
            if selected_card:
                print(f"\n✓ 选择了卡牌: {selected_card.name}")
                print(f"  稀有度: {['普通', '优秀', '稀有', '传说'][selected_card.rarity.value]}")
                
                # 将选中的卡牌加入玩家牌库
                player = self.battle.player
                if player:
                    # 如果玩家有牌库系统，使用牌库添加
                    if hasattr(player, 'card_library') and player.card_library:
                        # 先添加到牌库
                        player.card_library.add_card_to_library(selected_card)
                        print(f"  已加入牌库")
                        
                        # 尝试自动添加到卡组（如果符合条件）
                        if player.card_library.can_add_to_deck(selected_card.name):
                            if player.card_library.add_card_to_deck(selected_card.name):
                                print(f"  已自动添加到卡组")
                            else:
                                print(f"  无法自动添加到卡组（可能已达上限）")
                        else:
                            print(f"  未自动添加到卡组（可在卡组编辑界面手动添加）")
                    else:
                        # 原有逻辑（向后兼容）
                        if hasattr(player, 'deck'):
                            player.deck.append(selected_card)
                            print(f"  已加入牌库，当前牌库大小: {len(player.deck)}")
            else:
                print("\n✗ 跳过选择")
            
            # 清除掉落卡牌数据，防止再次触发选择界面
            self.battle.dropped_cards_for_selection = []
            print("[DEBUG] 已清除掉落卡牌数据")
            
            # 标记已经进入过卡组编辑，防止返回GameView后显示结束战斗按钮
            self._deck_edit_shown = True
            
            # 选择完成后，先检查是否有生命骰回血需要处理
            if hasattr(self.battle, 'hit_dice_recovery_queue') and self.battle.hit_dice_recovery_queue:
                print("[DEBUG] 战利品选择完成，准备显示生命骰回血UI")
                self._show_hit_dice_recovery()
            else:
                # 没有生命骰回血，直接进入卡组编辑界面
                self._show_deck_edit()
        
        # 导入战利品选择视图
        from loot_selection_view import LootSelectionView
        
        # 保存当前游戏视图引用，以便LootSelectionView可以返回
        self.window._game_view = self
        
        # 创建并显示战利品选择视图
        loot_view = LootSelectionView(dropped_cards, on_selection_complete)
        self.window.show_view(loot_view)
    
    def _show_deck_edit(self):
        """显示卡组编辑界面"""
        print("\n" + "*"*60)
        print("[DEBUG] >>> 显示卡组编辑UI <<<")
        print("*"*60)
        
        player = self.battle.player
        if not player:
            print("[ERROR] 玩家不存在，无法编辑卡组")
            return
        
        # 在显示卡组编辑界面之前，先将手牌和弃牌堆的卡牌回收到卡组
        print("\n[DEBUG] 进入卡组编辑前，先回收卡牌...")
        self._return_cards_to_deck()
        
        print(f"[DEBUG] 进入卡组编辑前的状态:")
        print(f"  - 卡组大小: {len(player.deck)}")
        print(f"  - 卡组列表: {[c.name for c in player.deck]}")
        print(f"  - 手牌数量: {len(player.hand)}")
        print(f"  - 弃牌堆数量: {len(player.discard_pile)}")
        if hasattr(player, 'card_library') and player.card_library:
            print(f"  - 牌库系统: 存在")
            print(f"  - 牌库卡牌: {list(player.card_library.library.keys())}")
        else:
            print(f"  - 牌库系统: 不存在")
        print("*"*60)
        
        def on_edit_complete():
            """编辑完成回调"""
            print(f"\n✓ 卡组编辑完成")
            print(f"  最终卡组大小: {len(player.deck)}")
            
            # 清除掉落卡牌数据（如果还有）
            self.battle.dropped_cards_for_selection = []
            
            # 编辑完成后，自动进入地图场景
            self._end_battle_and_start_map()
        
        # 导入卡组编辑视图
        from deck_edit_view import DeckEditView
        
        # 保存当前游戏视图引用
        self.window._game_view = self
        
        # 创建并显示卡组编辑视图
        deck_edit_view = DeckEditView(player, on_edit_complete)
        self.window.show_view(deck_edit_view)
    


"""
场景管理系统
提供不同游戏场景之间的切换机制
"""
import arcade
from typing import Optional
from battle_system import BattleSystem
from tile_map import TileMap
from ui_scale import S
from map_system import MapSystem
from map_view import MapView


class SceneView(arcade.View):
    """场景基类 - 所有游戏场景的父类"""
    
    def __init__(self, window=None):
        # 关键修复：传递window参数给父类
        super().__init__(window=window)
        self.window_width = 1920
        self.window_height = 1080
    
    def on_resize(self, width: int, height: int):
        """窗口尺寸变化"""
        self.window_width = width
        self.window_height = height
    
    def on_draw(self):
        """绘制场景（子类必须实现）"""
        raise NotImplementedError("子类必须实现on_draw方法")
    
    def switch_to_scene(self, new_scene: 'SceneView'):
        """切换到新场景"""
        self.window.show_view(new_scene)


class BattleSceneView(SceneView):
    """战斗场景"""
    
    def __init__(self, battle: BattleSystem, window=None, on_battle_end_callback=None):
        super().__init__(window=window)
        self.battle = battle
        self.on_battle_end_callback = on_battle_end_callback  # 战斗结束回调
        
        # 导入原有组件
        from game_view import CardView
        # 复用原有的CardView逻辑
        self.card_view = CardView(battle)
        
        # 设置战斗结束后的回调
        self._setup_battle_end_callback()
    
    def _setup_battle_end_callback(self):
        """设置战斗结束后的回调"""
        # 保存原始的on_update方法
        original_on_update = self.card_view.on_update
        
        def wrapped_on_update(delta_time):
            # 先执行原始的更新逻辑
            original_on_update(delta_time)
            
            # 检查战斗是否结束
            if self.battle.battle_finished and not hasattr(self, '_battle_end_handled'):
                self._battle_end_handled = True
                print("\n[战斗场景] 战斗结束，准备返回大地图")
                
                # 如果设置了回调函数，调用它
                if self.on_battle_end_callback:
                    self.on_battle_end_callback(self.battle)
                else:
                    # 默认行为：返回到大地图场景
                    self._return_to_map()
        
        # 替换on_update方法
        self.card_view.on_update = wrapped_on_update
    
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.card_view.on_resize(width, height)
    
    def on_draw(self):
        """绘制战斗场景"""
        self.card_view.on_draw()
    
    def on_mouse_motion(self, x, y, dx, dy):
        self.card_view.on_mouse_motion(x, y, dx, dy)
    
    def on_mouse_press(self, x, y, button, modifiers):
        self.card_view.on_mouse_press(x, y, button, modifiers)
    
    def on_mouse_release(self, x, y, button, modifiers):
        self.card_view.on_mouse_release(x, y, button, modifiers)
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.card_view.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
    
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.card_view.on_mouse_scroll(x, y, scroll_x, scroll_y)
    
    def on_key_press(self, key, modifiers):
        # 处理场景切换快捷键
        if key == arcade.key.M and (modifiers & arcade.key.MOD_SHIFT):
            # Shift+M: 切换到地图场景
            self._switch_to_map()
            return
        self.card_view.on_key_press(key, modifiers)
    
    def _switch_to_map(self):
        """切换到地图场景"""
        print("[DEBUG] 切换到地图场景")
        from scene_manager import MapSceneView
        map_scene = MapSceneView(self.battle, window=self.window)
        self.switch_to_scene(map_scene)
    
    def _return_to_map(self):
        """战斗结束后返回到大地图场景"""
        print("[战斗场景] 返回到大地图场景")
        
        # 获取玩家实体
        player_entity = None
        if self.battle.player_team:
            player_entity = self.battle.player_team[0]
        
        # 创建新的地图场景，并传入更新后的玩家实体
        from scene_manager import MapSceneView
        map_scene = MapSceneView(self.battle, window=self.window)
        
        # 更新地图场景中的玩家实体
        if player_entity and hasattr(map_scene.map_view, 'player_entity'):
            map_scene.map_view.player_entity = player_entity
            print(f"[战斗场景] 已更新玩家实体: {player_entity.name}")
        
        # 切换到地图场景
        self.switch_to_scene(map_scene)
    
    def on_update(self, delta_time: float):
        self.card_view.on_update(delta_time)
    



class NarrativeSceneView(SceneView):
    """叙事场景（大地图场景的雏形）"""
    
    def __init__(self, battle: BattleSystem, node_id: str, window=None):
        # 关键修复：确保在初始化前设置正确的窗口尺寸
        super().__init__(window=window)
        self.battle = battle
        self.node_id = node_id
        
        print(f"[DEBUG] NarrativeSceneView 初始化")
        print(f"[DEBUG] self.window = {self.window}")
        print(f"[DEBUG] window_width = {self.window_width}, window_height = {self.window_height}")
        
        # 导入叙事系统
        from narrative_renderer import NarrativeSceneRenderer
        from narrative_system import NarrativeNodeManager, NarrativeResultEngine
        from card_display import CardDisplay
        from ui_renderers import UIRenderer
        
        # 使用实际窗口尺寸初始化UI组件
        actual_width = self.window.width if self.window else self.window_width
        actual_height = self.window.height if self.window else self.window_height
        
        print(f"[DEBUG] 实际窗口尺寸: {actual_width} x {actual_height}")
        
        self.ui_renderer = UIRenderer(actual_width, actual_height)
        self.card_display = CardDisplay(self.ui_renderer)
        self.narrative_renderer = NarrativeSceneRenderer(actual_width, actual_height)
        self.narrative_node_manager = NarrativeNodeManager()
        self.NarrativeResultEngine = NarrativeResultEngine
        
        # 加载叙事节点
        try:
            self.narrative_node_manager.load_from_file("narrative_nodes.json")
            self.current_node = self.narrative_node_manager.get_node(node_id)
            if self.current_node:
                player = self.battle.player
                if player:
                    self.narrative_renderer.set_node(self.current_node, player)
                print(f"[叙事] 场景 '{self.current_node.title}' 已加载")
            else:
                print(f"[警告] 未找到节点: {node_id}")
                self.current_node = None
        except Exception as e:
            print(f"[错误] 加载叙事节点失败: {e}")
            self.current_node = None
    
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.ui_renderer.on_resize(width, height)
        self.narrative_renderer.on_resize(width, height)
    
    def on_draw(self):
        """绘制叙事场景（清屏效果：完全不绘制战斗UI）"""
        print(f"[DEBUG] NarrativeSceneView.on_draw called")
        print(f"[DEBUG] current_node: {self.current_node.title if self.current_node else None}")
        
        self.clear()
        
        # 只绘制叙事场景，不绘制任何战斗相关UI
        if self.current_node:
            # 绘制叙事场景视图
            self.narrative_renderer.draw()
            
            # 绘制过滤后的手牌（只显示互动卡牌）
            self.card_display.draw_hand(
                self.battle,
                narrative_mode=True,
                current_node=self.current_node
            )
        else:
            # 如果没有节点，显示错误信息
            arcade.draw_text(
                "错误：无法加载叙事节点",
                self.window_width // 2,
                self.window_height // 2,
                arcade.color.RED,
                S.font(24),
                anchor_x="center",
                anchor_y="center"
            )
    
    def on_mouse_motion(self, x, y, dx, dy):
        """鼠标移动 - 检查悬停"""
        if self.current_node:
            hovered = self.card_display.check_hover(x, y)
            # print(f"[DEBUG] Mouse motion: ({x}, {y}), hovered={hovered.name if hovered else None}")
    
    def on_mouse_press(self, x, y, button, modifiers):
        """鼠标点击 - 处理叙事交互和卡牌拖动开始"""
        if button == arcade.MOUSE_BUTTON_LEFT and self.current_node:
            # 先检查是否点击了卡牌（开始拖动）
            card = self.card_display.check_hover(x, y)
            # print(f"[DEBUG] Mouse press: ({x}, {y}), card={card.name if card else None}")
            if card:
                # 开始拖动卡牌
                self.card_display.start_drag(x, y)
                # print(f"[DEBUG] Start drag: {card.name}")
                return
            
            # 检查是否点击了选项
            action = self.narrative_renderer.handle_option_click(x, y)
            if action:
                self._handle_narrative_action(action)
                return
            
            # 检查是否点击了确定按钮
            if self.narrative_renderer.handle_confirm_click(x, y):
                self._handle_narrative_confirm()
                return
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """鼠标拖动 - 更新卡牌拖动位置"""
        if buttons & arcade.MOUSE_BUTTON_LEFT and self.current_node:
            if self.card_display.is_dragging():
                self.card_display.update_drag(x, y)
                # print(f"[DEBUG] Dragging: ({x}, {y})")
    
    def on_mouse_release(self, x, y, button, modifiers):
        """鼠标释放 - 处理卡牌拖放"""
        if button == arcade.MOUSE_BUTTON_LEFT and self.current_node:
            if self.card_display.is_dragging():
                dragged_card = self.card_display.end_drag(x, y)
                # print(f"[DEBUG] End drag: {dragged_card.name if dragged_card else None}")
                if dragged_card:
                    self._handle_card_drop_on_narrative(dragged_card)
                self.card_display.clear_drag()
    
    def on_key_press(self, key, modifiers):
        """键盘事件"""
        if key == arcade.key.ESCAPE:
            # ESC退出叙事场景，返回战斗场景或主菜单
            print("[叙事] 退出叙事场景")
            from main import CardGame
            # 这里可以返回到主菜单或其他场景
            # 暂时关闭窗口
            self.window.close()
    
    def on_update(self, delta_time: float):
        """更新逻辑"""
        self.card_display.update_animations()
    
    def _handle_narrative_action(self, action):
        """处理叙事动作选择"""
        print(f"\n[叙事] 选择动作: {action.name}")
        self.narrative_renderer.selected_action = action
        
        player = self.battle.player
        if not player:
            print("警告：未找到玩家实体")
            return
        
        # 执行检定
        dice_total, stat_bonus, final_result, outcome = self.NarrativeResultEngine.perform_check(
            action, player.stats
        )
        
        print(f"[叙事] 检定结果: 骰子={dice_total}, 加值={stat_bonus}, 最终={final_result}, 结果={outcome}")
        
        # 生成叙事结果
        result = self.NarrativeResultEngine.generate_result(
            self.current_node,
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
        """处理确定按钮点击"""
        print("\n[叙事] 点击确定按钮")
        
        if not self.narrative_renderer.current_result:
            print("警告：没有当前结果")
            return
        
        # 获取结果等级
        outcome_level = self.narrative_renderer.current_result.outcome_level
        
        # 查找下一节点
        next_node_id = self.current_node.next_nodes.get(outcome_level)
        
        if next_node_id:
            print(f"[叙事] 跳转到下一节点: {next_node_id}")
            # 切换到下一节点（创建新的NarrativeSceneView）
            new_narrative_scene = NarrativeSceneView(self.battle, next_node_id, window=self.window)
            self.switch_to_scene(new_narrative_scene)
        else:
            print(f"[叙事] 叙事结束（无下一节点）")
            # 叙事结束，可以返回主菜单或继续大地图探索
            # 暂时关闭窗口
            print("[叙事] 叙事流程结束，游戏将继续开发大地图功能...")
            self.window.close()
    
    def _handle_card_drop_on_narrative(self, card):
        """处理卡牌拖放到叙事场景"""
        print(f"\n[叙事] 卡牌拖放: {card.name}")
        
        if not self.current_node:
            return
        
        # 检查卡牌是否有叙事动作（通过卡牌的 tags 来匹配节点的 required_tags）
        for action in self.current_node.actions:
            if action.is_hidden and action.name not in self.narrative_renderer.revealed_hidden_actions:
                # 获取卡牌的标签值列表
                card_tag_values = [t.value if hasattr(t, 'value') else str(t) for t in card.tags]
                # 检查卡牌标签是否匹配隐藏动作所需的标签
                if any(req_tag in card_tag_values for req_tag in action.required_tags):
                    self.narrative_renderer.reveal_hidden_action(action.name)
                    print(f"[叙事] 揭示隐藏动作: {action.name}")
                    break


class MapSceneView(SceneView):
    """大地图场景 - 显示地图节点和连接，支持移动交互"""
    
    def __init__(self, battle: BattleSystem, window=None):
        super().__init__(window=window)
        self.battle = battle
        
        print(f"[DEBUG] MapSceneView.__init__ called")
        print(f"[DEBUG]   battle存在: {battle is not None}")
        if battle:
            print(f"[DEBUG]   battle.player存在: {hasattr(battle, 'player')}")
            if hasattr(battle, 'player'):
                print(f"[DEBUG]   玩家名称: {battle.player.name}")
        
        # 创建地图系统
        self.map_system = MapSystem()
        self.map_system.create_example_map()
        
        # 获取玩家实体（从战斗系统中）
        player_entity = battle.player if battle and hasattr(battle, 'player') else None
        print(f"[DEBUG]   player_entity提取结果: {player_entity is not None}")
        
        # 创建地图视图（传入玩家实体用于战斗触发）
        print(f"[DEBUG]   开始创建MapView...")
        self.map_view = MapView(
            self.map_system,
            window=self.window,
            player_entity=player_entity
        )
        print(f"[DEBUG]   MapView创建完成")
        
        print("[大地图] 场景已创建")
        if player_entity:
            print(f"[大地图] 玩家实体: {player_entity.name}")
        else:
            print("[大地图] 警告：未找到玩家实体，战斗触发将不可用")
    
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.map_view.on_resize(width, height)
    
    def on_draw(self):
        """绘制大地图场景"""
        self.map_view.on_draw()
    
    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.map_view.on_mouse_motion(x, y, dx, dy)
    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        self.map_view.on_mouse_press(x, y, button, modifiers)
    
    def on_key_press(self, key: int, modifiers: int):
        print(f"[DEBUG] MapSceneView.on_key_press called: key={key}, modifiers={modifiers}")
        
        if key == arcade.key.ESCAPE:
            # ESC键：退出游戏
            print("[大地图] 退出游戏")
            self.window.close()
        else:
            # 将其他按键事件传递给MapView
            print(f"[DEBUG] 将按键事件传递给MapView")
            self.map_view.on_key_press(key, modifiers)

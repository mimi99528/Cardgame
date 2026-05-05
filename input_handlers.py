"""
输入处理模块
负责鼠标和键盘事件的处理
"""
import arcade
from typing import Optional, Tuple
from models import Card, Entity
from battle_system import BattleSystem
from config import TargetType
from tile_map import TileMap


class InputHandler:
    """输入处理器 - 处理鼠标和键盘事件"""
    
    def __init__(self, battle: BattleSystem, tile_map: TileMap, card_display, inventory_renderer=None, equipment_renderer=None):
        """
        初始化输入处理器
        
        Args:
            battle: 战斗系统实例
            tile_map: 瓦片地图实例
            card_display: 卡牌显示器实例
            inventory_renderer: 背包渲染器实例（可选）
            equipment_renderer: 装备渲染器实例（可选）
        """
        self.battle = battle
        self.tile_map = tile_map
        self.card_display = card_display
        self.inventory_renderer = inventory_renderer
        self.equipment_renderer = equipment_renderer
        
        # 状态变量
        self.hovered_entity: Optional[Entity] = None
        self.selected_card: Optional[Card] = None
        self.target_selection_mode = False
        self.first_click_pos: Optional[Tuple[int, int]] = None
        
        # 移动卡牌相关
        self.movement_mode = False  # 是否在移动卡牌模式
        self.valid_move_positions: list = []  # 可移动位置列表
        self.current_move_path: Optional[list] = None  # 当前悬停的路径
        
        # 拖动相关
        self.drag_mode = False  # 是否在拖动模式
        self.dragged_card_for_target: Optional[Card] = None  # 用于拖动的卡牌
    
    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float,
                       map_offset_x: float, map_offset_y: float,
                       entity_positions, window_width: float = None, window_height: float = None):
        """
        处理鼠标移动事件
        
        Args:
            x, y: 鼠标坐标（屏幕坐标）
            dx, dy: 鼠标移动增量
            map_offset_x, map_offset_y: 地图偏移量（已废弃，保留兼容性）
            entity_positions: 实体位置映射字典
            window_width, window_height: 窗口尺寸（用于坐标转换）
        """
        # 如果装备界面打开，更新装备界面的悬停状态
        if self.equipment_renderer and self.equipment_renderer.is_visible():
            # 如果正在拖动装备，更新拖动位置
            print(f"Updating equipment renderer: dragged_item={self.equipment_renderer.dragged_item is not None}, pos=({x}, {y})")
            if self.equipment_renderer.dragged_item:
                print(f"  -> Calling update_drag with ({x}, {y})")
                self.equipment_renderer.update_drag(x, y)
            else:
                self.equipment_renderer.update_hover(x, y)
            return

        # 如果背包界面打开，更新背包的悬停状态
        if self.inventory_renderer and self.inventory_renderer.is_visible():
            self.inventory_renderer.update_hover(x, y)
            return
        
        # 检查卡牌悬停（如果不在拖动模式）
        if not self.drag_mode:
            self.card_display.check_hover(x, y)
        
        # 如果在移动卡牌模式，显示路径
        if self.movement_mode and self.current_move_path:
            # 使用相机系统转换坐标
            if window_width and window_height:
                grid_x, grid_y = self.tile_map.screen_to_grid(x, y, window_width, window_height)
            else:
                # 向后兼容：如果没有提供窗口尺寸，使用旧方法
                adjusted_x = x - map_offset_x
                adjusted_y = y - map_offset_y
                tile = self.tile_map.get_tile_at_pixel(adjusted_x, adjusted_y)
                if tile:
                    grid_x, grid_y = tile.x, tile.y
                else:
                    return
            
            if (grid_x, grid_y) in self.valid_move_positions:
                # 计算从当前位置到悬停位置的路径
                current_entity = self.battle.current_entity
                if current_entity:
                    path = self.tile_map.find_path_astar(
                        current_entity.position, 
                        (grid_x, grid_y),
                        [e.position for e in self.battle.player_team + self.battle.enemy_team 
                         if e.is_alive() and e != current_entity]
                    )
                    if path:
                        self.tile_map.highlight_path(path)
                        self.current_move_path = path
                    else:
                        self.tile_map.reset_highlights()
                        self.current_move_path = None
                return
        
        # 检查实体悬停
        self.hovered_entity = None
        
        # 使用相机系统转换坐标
        if window_width and window_height:
            grid_x, grid_y = self.tile_map.screen_to_grid(x, y, window_width, window_height)
        else:
            # 向后兼容
            adjusted_x = x - map_offset_x
            adjusted_y = y - map_offset_y
            tile = self.tile_map.get_tile_at_pixel(adjusted_x, adjusted_y)
            if tile:
                grid_x, grid_y = tile.x, tile.y
            else:
                return
        
        # 检查是否有实体在该位置
        for entity in self.battle.player_team + self.battle.enemy_team:
            if entity.position == (grid_x, grid_y) and entity.is_alive():
                self.hovered_entity = entity
                break
    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int,
                      map_offset_x: float, map_offset_y: float,
                      window_width: float = None, window_height: float = None):
        """
        处理鼠标点击事件
        
        Args:
            x, y: 鼠标坐标（屏幕坐标）
            button: 鼠标按钮
            modifiers: 修饰键
            map_offset_x, map_offset_y: 地图偏移量（已废弃，保留兼容性）
            window_width, window_height: 窗口尺寸（用于坐标转换）
        """
        # 如果装备界面打开，处理装备界面的点击
        if self.equipment_renderer and self.equipment_renderer.is_visible():
            # 左键：开始拖动或装备物品
            if button == arcade.MOUSE_BUTTON_LEFT:
                # 检查是否点击了装备槽位（开始拖动）
                slot = self.equipment_renderer.get_slot_at_pos(x, y)
                if slot:
                    # 开始从槽位拖动
                    if self.equipment_renderer.start_drag_from_slot(slot, x, y):
                        print(f"开始拖动槽位 {slot.value} 的装备")
                        return
                
                # 检查是否点击了背包物品（开始拖动）
                item_index = self.equipment_renderer.get_inventory_item_at_pos(x, y)
                if item_index is not None:
                    # 开始从背包拖动
                    if self.equipment_renderer.start_drag_from_inventory(item_index, x, y):
                        print(f"开始拖动背包物品")
                        return
                
                # 如果没有点击可拖动的物品，处理普通点击
                self._handle_equipment_interface_click(x, y, button)
            # 右键：卸下装备
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                self._handle_equipment_interface_click(x, y, button)
            return
        
        # 如果背包界面打开，处理背包的点击
        if self.inventory_renderer and self.inventory_renderer.is_visible():
            self._handle_inventory_interface_click(x, y, button)
            return
        
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
        
        if self.battle.battle_finished:
            return
        
        current_entity = self.battle.current_entity
        
        # 如果在拖动模式，处理拖动结束
        if self.drag_mode and self.dragged_card_for_target:
            self._handle_drag_end(x, y, map_offset_x, map_offset_y, window_width, window_height)
            return
        
        # 检查是否点击了卡牌
        card_clicked = self.card_display.check_click(x, y)
        
        if card_clicked:
            # 如果是有目标的卡牌，启动拖动
            if card_clicked.target_type in [TargetType.ENEMY, TargetType.ALLY, TargetType.ANY]:
                # 检查是否处于移动模式
                if self.movement_mode:
                    print("当前处于移动模式，无法拖动卡牌")
                    return
                
                # 启动拖动（不在这里验证，在拖动结束时验证）
                self.card_display.start_drag(x, y)
                self.drag_mode = True
                self.dragged_card_for_target = card_clicked
                print(f"开始拖动卡牌: {card_clicked.name}，拖动到目标位置释放")
            else:
                # 其他卡牌正常点击处理
                self._handle_card_click(card_clicked, current_entity)
        else:
            # 检查是否点击了瓦片地图区域
            self._handle_tile_click(x, y, map_offset_x, map_offset_y, current_entity, window_width, window_height)
    
    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int,
                        map_offset_x: float, map_offset_y: float,
                        window_width: float = None, window_height: float = None):
        """
        处理鼠标释放事件
        
        Args:
            x, y: 鼠标坐标（屏幕坐标）
            button: 鼠标按钮
            modifiers: 修饰键
            map_offset_x, map_offset_y: 地图偏移量（已废弃，保留兼容性）
            window_width, window_height: 窗口尺寸（用于坐标转换）
        """
        # 如果装备界面打开且正在拖动装备
        if self.equipment_renderer and self.equipment_renderer.is_visible():
            if self.equipment_renderer.dragged_item and button == arcade.MOUSE_BUTTON_LEFT:
                # 检查释放位置是否在某个槽位上
                target_slot = self.equipment_renderer.get_slot_at_pos(x, y)
                
                # 结束拖动
                success, message = self.equipment_renderer.end_drag(target_slot)
                print(message)
                return
        
        # 处理卡牌拖动释放
        if self.drag_mode and self.dragged_card_for_target and button == arcade.MOUSE_BUTTON_LEFT:
            self._handle_drag_end(x, y, map_offset_x, map_offset_y, window_width, window_height)
    
    def _handle_card_click(self, card: Card, current_entity: Entity):
        """处理卡牌点击（非拖动情况）"""
        # 如果是移动卡牌
        if card.is_movement:
            # 如果已经在移动模式中，点击移动卡牌应该退出
            if self.movement_mode:
                print("点击移动卡牌，退出移动模式")
                self._exit_movement_mode()
                return
            else:
                # 否则进入移动模式
                self._handle_movement_card(card, current_entity)
                return
        
        self.selected_card = card
        print(f"选择了卡牌: {card.name}")
        
        # 如果卡牌目标是自身，直接使用
        if card.target_type == TargetType.SELF:
            print(f"对自身使用卡牌 {card.name}")
            success, is_permanent, log_entries = self.battle.play_card(card, current_entity)
            if success:
                print("卡牌使用成功！")
                # 如果是常驻卡牌，启动上升动画
                if is_permanent:
                    self.card_display.start_rising_animation(card, duration=0.5)
            else:
                print("卡牌使用失败！")
            self.selected_card = None
        else:
            # 其他目标类型，进入目标选择模式
            # 获取攻击范围形状配置
            attack_range_shape = self.battle.get_card_attack_range_shape(card)
            
            # 使用新的高亮方法显示攻击范围
            self.tile_map.highlight_attack_range(
                current_entity.position[0], 
                current_entity.position[1], 
                attack_range_shape
            )
            self.target_selection_mode = True
    
    def _handle_movement_card(self, card: Card, current_entity: Entity):
        """处理移动卡牌"""
        if not current_entity or current_entity.control_type.value != "player":
            return
        
        # 检查AP是否足够
        if current_entity.ap < card.ap_cost:
            print(f"AP不足！需要{card.ap_cost}，剩余{current_entity.ap}")
            return
        
        # 进入移动模式
        self.movement_mode = True
        self.selected_card = card
        
        # 获取所有其他实体的位置
        all_entities = self.battle.player_team + self.battle.enemy_team
        other_positions = [e.position for e in all_entities if e != current_entity and e.is_alive()]
        
        # 计算可移动位置
        self.valid_move_positions = self.tile_map.get_valid_moves_with_md(
            current_entity.position,
            current_entity.md,
            other_positions
        )
        
        # 高亮显示可移动范围
        self.tile_map.highlight_move_range(
            current_entity.position[0],
            current_entity.position[1],
            self.valid_move_positions
        )
        
        print(f"移动模式已激活，可移动到{len(self.valid_move_positions)}个位置")
    
    def _handle_movement_card_target(self, target_x: int, target_y: int):
        """处理移动卡牌的目标选择"""
        if not self.selected_card or not self.movement_mode:
            return
        
        current_entity = self.battle.current_entity
        if not current_entity:
            return
        
        # 检查目标是否在可移动范围内
        if (target_x, target_y) not in self.valid_move_positions:
            print("目标位置不在可移动范围内！")
            self._exit_movement_mode()
            return
        
        # 执行移动
        success = self.battle.move_entity(current_entity, (target_x, target_y), self.tile_map)
        
        if success:
            # 扣除AP
            current_entity.ap -= self.selected_card.ap_cost
            print(f"使用了移动卡牌 {self.selected_card.name}，消耗{self.selected_card.ap_cost}AP")
            
            # 检查是否是常驻卡牌
            is_permanent = self.selected_card in current_entity.permanent_cards
            
            # 从手牌中移除卡牌
            if self.selected_card in current_entity.hand:
                current_entity.hand.remove(self.selected_card)
            
            # 如果是常驻卡牌，立即重新加入手牌并触发动画
            if is_permanent:
                current_entity.hand.append(self.selected_card)
                # 触发上升动画
                self.card_display.start_rising_animation(self.selected_card, duration=0.5)
                print(f"常驻卡牌 {self.selected_card.name} 已重新加入手牌")
        else:
            print("移动失败！")
        
        self._exit_movement_mode()
    
    def _exit_movement_mode(self):
        """退出移动模式"""
        self.movement_mode = False
        self.selected_card = None
        self.valid_move_positions = []
        self.current_move_path = None
        self.tile_map.reset_highlights()
    
    def _handle_drag_end(self, x: float, y: float, map_offset_x: float, map_offset_y: float,
                        window_width: float = None, window_height: float = None):
        """处理拖动结束"""
        if not self.dragged_card_for_target:
            self.drag_mode = False
            return
        
        # 验证卡牌是否仍然在当前实体的手牌中
        current_entity = self.battle.current_entity
        if not current_entity or self.dragged_card_for_target not in current_entity.hand:
            print("卡牌已不在手牌中，取消出牌")
            self.drag_mode = False
            self.dragged_card_for_target = None
            return
        
        # 计算鼠标位置对应的瓦片（使用相机系统）
        if window_width and window_height:
            grid_x, grid_y = self.tile_map.screen_to_grid(x, y, window_width, window_height)
        else:
            # 向后兼容
            adjusted_x = x - map_offset_x
            adjusted_y = y - map_offset_y
            tile = self.tile_map.get_tile_at_pixel(adjusted_x, adjusted_y)
            if tile:
                grid_x, grid_y = tile.x, tile.y
            else:
                print("拖动到无效位置，取消出牌")
                self.drag_mode = False
                self.dragged_card_for_target = None
                return
        
        tile = self.tile_map.get_tile(grid_x, grid_y)
        if not tile:
            print("拖动到无效位置，取消出牌")
            self.drag_mode = False
            self.dragged_card_for_target = None
            return
        
        if not current_entity:
            self.drag_mode = False
            self.dragged_card_for_target = None
            return
        
        card = self.dragged_card_for_target
        
        # 根据卡牌目标类型确定目标实体
        target_entity = self._find_target_entity(grid_x, grid_y, current_entity)
        
        if target_entity:
            # 检查距离
            distance = abs(grid_x - current_entity.position[0]) + abs(grid_y - current_entity.position[1])
            max_distance = self._get_card_range(card)
            
            if distance <= max_distance:
                print(f"拖动打出卡牌 {card.name} 攻击位置 ({grid_x}, {grid_y})")
                success, is_permanent, log_entries = self.battle.play_card(card, target_entity)
                if success:
                    print("卡牌使用成功！")
                    # 如果是常驻卡牌，启动上升动画
                    if is_permanent:
                        self.card_display.start_rising_animation(card, duration=0.5)
            else:
                print(f"目标超出范围！最大距离: {max_distance}, 实际距离: {distance}")
        else:
            print("目标位置上没有有效实体，取消出牌")
        
        # 清除拖动状态
        self.drag_mode = False
        self.dragged_card_for_target = None
    
    def _handle_tile_click(self, x: float, y: float, map_offset_x: float, 
                          map_offset_y: float, current_entity: Entity,
                          window_width: float = None, window_height: float = None):
        """处理瓦片点击"""
        # 使用相机系统转换坐标
        if window_width and window_height:
            grid_x, grid_y = self.tile_map.screen_to_grid(x, y, window_width, window_height)
        else:
            # 向后兼容
            adjusted_x = x - map_offset_x
            adjusted_y = y - map_offset_y
            tile = self.tile_map.get_tile_at_pixel(adjusted_x, adjusted_y)
            if tile:
                grid_x, grid_y = tile.x, tile.y
            else:
                return
        
        tile = self.tile_map.get_tile(grid_x, grid_y)
        if not tile:
            return
        
        # 如果在移动模式，执行移动
        if self.movement_mode:
            self._handle_movement_card_target(grid_x, grid_y)
            return
        
        # if self.target_selection_mode:
        #     # 第二次点击，确定目标
        #     self._handle_target_selection(grid_x, grid_y)
        #     self.target_selection_mode = False
        #     self.first_click_pos = None
        #     self.tile_map.reset_highlights()
        # else:
        #     # 第一次点击，进入目标选择模式或移动
        #     # 不再显示默认范围，因为卡牌选择时会自动显示正确的攻击范围
        #     self.first_click_pos = (grid_x, grid_y)
        #     self.target_selection_mode = True
    
    def _handle_target_selection(self, target_x: int, target_y: int):
        """处理目标选择"""
        if not self.selected_card:
            # 没有选择卡牌，尝试移动
            self._handle_movement(target_x, target_y)
            return
        
        current_entity = self.battle.current_entity
        if not current_entity:
            return
        
        # 检查目标是否在卡牌的有效范围内
        distance = abs(target_x - current_entity.position[0]) + \
                  abs(target_y - current_entity.position[1])
        
        max_distance = self._get_card_range(self.selected_card)
        
        if distance <= max_distance:
            print(f"使用卡牌 {self.selected_card.name} 攻击位置 ({target_x}, {target_y})")
            
            # 根据卡牌的目标类型确定目标实体
            target_entity = self._find_target_entity(target_x, target_y, current_entity)
            
            if target_entity:
                success, is_permanent, log_entries = self.battle.play_card(self.selected_card, target_entity)
                if success:
                    print("卡牌使用成功！")
                    # 如果是常驻卡牌，启动上升动画
                    if is_permanent:
                        self.card_display.start_rising_animation(self.selected_card, duration=0.5)
        else:
            print(f"目标超出范围！最大距离: {max_distance}, 实际距离: {distance}")
        
        self.selected_card = None
    
    def _find_target_entity(self, target_x: int, target_y: int, 
                           current_entity: Entity) -> Optional[Entity]:
        """根据目标类型查找目标实体"""
        # 优先使用拖动的卡牌，否则使用选中的卡牌
        card = self.dragged_card_for_target if self.drag_mode else self.selected_card
        
        if not card:
            print("错误：没有选中或拖动的卡牌")
            return None
        
        if card.target_type == TargetType.SELF:
            return current_entity
        
        elif card.target_type == TargetType.ENEMY:
            for enemy in self.battle.enemy_team:
                if enemy.position == (target_x, target_y) and enemy.is_alive():
                    print(f"攻击敌人 {enemy.name}！")
                    return enemy
            print("目标不在敌人位置上")
        
        elif card.target_type == TargetType.ALLY:
            for ally in self.battle.player_team:
                if ally.position == (target_x, target_y) and ally.is_alive():
                    print(f"对友军 {ally.name} 使用卡牌 {card.name}")
                    return ally
            print("目标不在友军位置上")
        
        elif card.target_type == TargetType.ANY:
            for entity in self.battle.player_team + self.battle.enemy_team:
                if entity.position == (target_x, target_y) and entity.is_alive():
                    print(f"对 {entity.name} 使用卡牌 {card.name}")
                    return entity
            print("目标位置上没有实体")
        
        else:
            # 默认作为敌人处理
            for enemy in self.battle.enemy_team:
                if enemy.position == (target_x, target_y) and enemy.is_alive():
                    print(f"攻击敌人 {enemy.name}！")
                    return enemy
            print("目标不在敌人位置上")
        
        return None
    
    def _handle_movement(self, target_x: int, target_y: int):
        """处理移动逻辑"""
        current_entity = self.battle.current_entity
        if not current_entity or current_entity.control_type.value != "player":
            return
        
        # 检查是否是敌人位置
        is_enemy = any(enemy.position == (target_x, target_y) 
                      for enemy in self.battle.enemy_team if enemy.is_alive())
        
        if is_enemy:
            print("攻击敌人！（未选择卡牌）")
        else:
            success = self.battle.move_entity(current_entity, (target_x, target_y), 
                                            self.tile_map)
            if success:
                print(f"{current_entity.name}移动到: ({target_x}, {target_y})")
            else:
                print(f"无法移动到: ({target_x}, {target_y})")
    
    def _get_card_range(self, card: Card) -> int:
        """根据卡牌类型获取有效距离"""
        # 如果有atk_dis属性，使用它
        if hasattr(card, 'atk_dis') and card.atk_dis:
            return card.atk_dis
        
        default_range = 3
        
        if card.card_type.value in ["atk_phy", "atk_mag"]:
            return 5
        elif card.card_type.value == "blk":
            return 0
        elif card.card_type.value == "hel":
            return 3
        else:
            return default_range
    
    def on_key_press(self, key: int, modifiers: int):
        """
        处理键盘按键事件
        
        Args:
            key: 按下的键
            modifiers: 修饰键
        """
        # 调试信息：显示按键信息
        # print(f"按键: {key} (B键={arcade.key.B}, ESC={arcade.key.ESCAPE}, SPACE={arcade.key.SPACE})")
        
        if key == arcade.key.ESCAPE:
            # 如果背包打开，先关闭背包
            if self.inventory_renderer and self.inventory_renderer.is_visible():
                self.inventory_renderer.close_inventory()
                return False
            # 如果装备界面打开，关闭装备界面
            elif self.equipment_renderer and self.equipment_renderer.is_visible():
                self.equipment_renderer.close()
                return False
            elif self.battle.battle_finished:
                # 返回True表示应该关闭窗口
                return True
        
        elif key == arcade.key.SPACE:
            if not self.battle.battle_finished and self.battle.is_player_turn:
                self.battle.skip_turn()
        
        elif key == arcade.key.B:
            # B键打开/关闭背包
            if self.inventory_renderer:
                if not self.battle.current_entity:
                    print("警告：当前没有活动实体，无法打开背包")
                    return False
                
                player = self.battle.current_entity
                if not hasattr(player, 'inventory'):
                    print("警告：当前实体没有背包系统")
                    return False
                
                was_visible = self.inventory_renderer.is_visible()
                self.inventory_renderer.toggle_inventory(player.inventory)
                is_visible = self.inventory_renderer.is_visible()
                
                if is_visible and not was_visible:
                    print(f"背包已打开 - {player.name}")
                    info = player.inventory.get_usage_info()
                    print(f"  体积: {info['volume_used']}/{info['volume_max']}")
                    print(f"  重量: {info['weight_used']:.1f}/{info['weight_max']:.1f}")
                    print(f"  物品数: {info['item_count']}")
                elif not is_visible and was_visible:
                    print("背包已关闭")
            else:
                print("错误：背包渲染器未初始化")
        
        elif key == arcade.key.TAB:
            # Tab键打开/关闭装备界面
            if self.equipment_renderer:
                if not self.battle.current_entity:
                    print("警告：当前没有活动实体，无法打开装备界面")
                    return False
                
                player = self.battle.current_entity
                
                was_visible = self.equipment_renderer.is_visible()
                self.equipment_renderer.toggle_visibility(player)
                is_visible = self.equipment_renderer.is_visible()
                
                if is_visible and not was_visible:
                    print(f"装备界面已打开 - {player.name}")
                elif not is_visible and was_visible:
                    print("装备界面已关闭")
            else:
                print("错误：装备渲染器未初始化")
        
        return False
    
    def clear_drag_states(self):
        """清除所有拖动相关状态（用于回合切换时）"""
        self.drag_mode = False
        self.dragged_card_for_target = None
        self.selected_card = None
        self.target_selection_mode = False
        self.movement_mode = False
        self.valid_move_positions = []
        self.current_move_path = None
        # 彻底清除卡牌显示器中的所有卡牌引用
        self.card_display.clear_all_card_references()
    
    def _handle_equipment_interface_click(self, x: float, y: float, button: int):
        """处理装备界面的点击"""
        from equipment_manager import EquipmentSlot
        from inventory import ItemType
        
        if not self.equipment_renderer or not self.battle.current_entity:
            return
        
        entity = self.battle.current_entity
        equip_mgr = entity.equipment_manager
        
        # 右键点击：卸下装备
        if button == arcade.MOUSE_BUTTON_RIGHT:
            slot = self.equipment_renderer.get_slot_at_pos(x, y)
            if slot:
                success, message, old_item = equip_mgr.unequip_item(slot)
                print(message)
                
                # 如果有卸下的物品，放回背包
                if old_item and hasattr(entity, 'inventory'):
                    entity.inventory.add_item(old_item)
                    print(f"已将 {old_item.name} 放回背包")
            return
        
        # 左键点击：装备物品
        if button == arcade.MOUSE_BUTTON_LEFT:
            # 检查是否点击了背包中的物品
            item_index = self.equipment_renderer.get_inventory_item_at_pos(x, y)
            if item_index is not None and hasattr(entity, 'inventory'):
                inventory = entity.inventory
                equippable_items = [
                    item for item in inventory.items 
                    if item.item_type in [ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY]
                ]
                
                if 0 <= item_index < len(equippable_items):
                    item = equippable_items[item_index]
                    
                    # 根据物品类型确定槽位
                    if item.item_type == ItemType.WEAPON:
                        target_slot = EquipmentSlot.WEAPON
                    elif item.item_type == ItemType.ARMOR:
                        target_slot = EquipmentSlot.BODY
                    elif item.item_type == ItemType.ACCESSORY:
                        target_slot = EquipmentSlot.ACCESSORY
                    else:
                        return
                    
                    # 尝试装备（传入entity用于AP检查）
                    success, message, old_item = equip_mgr.swap_equipment(item, target_slot, entity)
                    print(message)
                    
                    if success:
                        # 从背包中移除物品
                        inventory.remove_item(item)
                        
                        # 如果有旧装备，放回背包
                        if old_item:
                            inventory.add_item(old_item)
                            print(f"已将 {old_item.name} 放回背包")
            
            # 检查是否点击了装备槽位（卸下装备）
            slot = self.equipment_renderer.get_slot_at_pos(x, y)
            if slot:
                success, message, old_item = equip_mgr.unequip_item(slot)
                print(message)
                
                # 如果有卸下的物品，放回背包
                if old_item and hasattr(entity, 'inventory'):
                    entity.inventory.add_item(old_item)
                    print(f"已将 {old_item.name} 放回背包")
    
    def _handle_inventory_interface_click(self, x: float, y: float, button: int):
        """处理背包界面的点击"""
        # 目前背包界面只支持查看，后续可以添加拖拽等功能
        pass

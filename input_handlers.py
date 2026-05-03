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
    
    def __init__(self, battle: BattleSystem, tile_map: TileMap, card_display):
        """
        初始化输入处理器
        
        Args:
            battle: 战斗系统实例
            tile_map: 瓦片地图实例
            card_display: 卡牌显示器实例
        """
        self.battle = battle
        self.tile_map = tile_map
        self.card_display = card_display
        
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
                       entity_positions):
        """
        处理鼠标移动事件
        
        Args:
            x, y: 鼠标坐标
            dx, dy: 鼠标移动增量
            map_offset_x, map_offset_y: 地图偏移量
            entity_positions: 实体位置映射字典
        """
        # 检查卡牌悬停（如果不在拖动模式）
        if not self.drag_mode:
            self.card_display.check_hover(x, y)
        
        # 如果在移动卡牌模式，显示路径
        if self.movement_mode and self.current_move_path:
            adjusted_x = x - map_offset_x
            adjusted_y = y - map_offset_y
            tile = self.tile_map.get_tile_at_pixel(adjusted_x, adjusted_y)
            
            if tile and (tile.x, tile.y) in self.valid_move_positions:
                # 计算从当前位置到悬停位置的路径
                current_entity = self.battle.current_entity
                if current_entity:
                    path = self.tile_map.find_path_astar(
                        current_entity.position, 
                        (tile.x, tile.y),
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
        adjusted_x = x - map_offset_x
        adjusted_y = y - map_offset_y
        tile = self.tile_map.get_tile_at_pixel(adjusted_x, adjusted_y)
        
        if tile:
            for entity in self.battle.player_team + self.battle.enemy_team:
                if entity.position == (tile.x, tile.y) and entity.is_alive():
                    self.hovered_entity = entity
                    break
    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int,
                      map_offset_x: float, map_offset_y: float):
        """
        处理鼠标点击事件
        
        Args:
            x, y: 鼠标坐标
            button: 鼠标按钮
            modifiers: 修饰键
            map_offset_x, map_offset_y: 地图偏移量
        """
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
        
        if self.battle.battle_finished:
            return
        
        current_entity = self.battle.current_entity
        
        # 如果在拖动模式，处理拖动结束
        if self.drag_mode and self.dragged_card_for_target:
            self._handle_drag_end(x, y, map_offset_x, map_offset_y)
            return
        
        # 检查是否点击了卡牌
        card_clicked = self.card_display.check_click(x, y)
        
        if card_clicked:
            # 如果是有目标的卡牌，启动拖动
            if card_clicked.target_type in [TargetType.ENEMY, TargetType.ALLY, TargetType.ANY]:
                self.card_display.start_drag(x, y)
                self.drag_mode = True
                self.dragged_card_for_target = card_clicked
                print(f"开始拖动卡牌: {card_clicked.name}，拖动到目标位置释放")
            else:
                # 其他卡牌正常点击处理
                self._handle_card_click(card_clicked, current_entity)
        else:
            # 检查是否点击了瓦片地图区域
            self._handle_tile_click(x, y, map_offset_x, map_offset_y, current_entity)
    
    def _handle_card_click(self, card: Card, current_entity: Entity):
        """处理卡牌点击（非拖动情况）"""
        # 如果是移动卡牌
        if card.is_movement:
            self._handle_movement_card(card, current_entity)
            return
        
        self.selected_card = card
        print(f"选择了卡牌: {card.name}")
        
        # 如果卡牌目标是自身，直接使用
        if card.target_type == TargetType.SELF:
            print(f"对自身使用卡牌 {card.name}")
            success, is_permanent = self.battle.play_card(card, current_entity)
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
            card_range = self._get_card_range(card)
            self.tile_map.highlight_range(current_entity.position[0], 
                                        current_entity.position[1], 
                                        card_range)
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
    
    def _handle_drag_end(self, x: float, y: float, map_offset_x: float, map_offset_y: float):
        """处理拖动结束"""
        if not self.dragged_card_for_target:
            self.drag_mode = False
            return
        
        # 计算鼠标位置对应的瓦片
        adjusted_x = x - map_offset_x
        adjusted_y = y - map_offset_y
        tile = self.tile_map.get_tile_at_pixel(adjusted_x, adjusted_y)
        
        if not tile:
            print("拖动到无效位置，取消出牌")
            self.drag_mode = False
            self.dragged_card_for_target = None
            return
        
        current_entity = self.battle.current_entity
        if not current_entity:
            self.drag_mode = False
            self.dragged_card_for_target = None
            return
        
        card = self.dragged_card_for_target
        
        # 根据卡牌目标类型确定目标实体
        target_entity = self._find_target_entity(tile.x, tile.y, current_entity)
        
        if target_entity:
            # 检查距离
            distance = abs(tile.x - current_entity.position[0]) + abs(tile.y - current_entity.position[1])
            max_distance = self._get_card_range(card)
            
            if distance <= max_distance:
                print(f"拖动打出卡牌 {card.name} 攻击位置 ({tile.x}, {tile.y})")
                success, is_permanent = self.battle.play_card(card, target_entity)
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
                          map_offset_y: float, current_entity: Entity):
        """处理瓦片点击"""
        adjusted_x = x - map_offset_x
        adjusted_y = y - map_offset_y
        tile = self.tile_map.get_tile_at_pixel(adjusted_x, adjusted_y)
        
        if not tile:
            return
        
        # 如果在移动模式，执行移动
        if self.movement_mode:
            self._handle_movement_card_target(tile.x, tile.y)
            return
        
        if self.target_selection_mode:
            # 第二次点击，确定目标
            self._handle_target_selection(tile.x, tile.y)
            self.target_selection_mode = False
            self.first_click_pos = None
            self.tile_map.reset_highlights()
        else:
            # 第一次点击，进入目标选择模式或移动
            self.first_click_pos = (tile.x, tile.y)
            self.target_selection_mode = True
            self.tile_map.highlight_range(tile.x, tile.y, 3)
    
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
                success, is_permanent = self.battle.play_card(self.selected_card, target_entity)
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
        if key == arcade.key.ESCAPE:
            if self.battle.battle_finished:
                # 返回True表示应该关闭窗口
                return True
        
        elif key == arcade.key.SPACE:
            if not self.battle.battle_finished and self.battle.is_player_turn:
                self.battle.skip_turn()
        
        return False

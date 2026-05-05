"""
战斗系统模块
管理回合制战斗逻辑
"""
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
import time

from models import Entity, Card, Buff, ControlType
from config import CONSTANTS


@dataclass
class BattleLog:
    """战斗日志"""
    entries: List[Tuple[str, int, str]] = field(default_factory=list)  # (message, level, color_key)
    
    def add(self, message: str, level: int = 0, color_key: str = "normal"):
        """
        添加日志条目
        
        Args:
            message: 日志消息
            level: 日志级别 (0=所有级别都显示, 1=normal及以上, 2=仅verbose)
            color_key: 颜色键值 ("critical_success", "success", "partial_success", "failure", "critical_failure", "normal")
        """
        from config import CONSTANTS
        log_level = CONSTANTS.LOG_LEVEL
        print(message, )
        # 根据日志级别决定是否记录
        should_add = False
        if log_level.value == "simple":
            # simple模式只记录level=0的消息
            if level == 0:
                should_add = True
        elif log_level.value == "normal":
            # normal模式记录level=0和level=1的消息
            if level <= 1:
                should_add = True
        else:  # verbose
            # verbose模式记录所有消息
            should_add = True
        
        if should_add:
            self.entries.append((message, level, color_key))
    
    def get_last_entries(self, count: int = 10) -> List[Tuple[str, int, str]]:
        """获取最近的日志条目"""
        return self.entries[-count:]
    
    def clear(self):
        """清空日志"""
        self.entries.clear()
    
    def __str__(self):
        # 返回最近20条日志的消息部分（不含颜色和级别）
        return "\n".join([entry[0] for entry in self.entries[-20:]])


class BattleSystem:
    """战斗系统管理器"""
    
    def __init__(self, player_team: List[Entity], enemy_team: List[Entity], tile_map=None):
        self.player_team = player_team
        self.enemy_team = enemy_team
        self.tile_map = tile_map  # 保存真实的地图引用
        
        # 重置所有实体状态
        for entity in player_team + enemy_team:
            entity.reset_for_battle()
        
        self.current_round = 0
        self.battle_log = BattleLog()
        self.is_player_turn = True
        self.battle_finished = False
        self.winner: Optional[List[Entity]] = None
        
        # 当前行动的实体索引
        self.current_entity_index = 0
        self.all_entities: List[Entity] = []  # 所有实体的行动顺序列表
        
        # AI出牌相关
        self.last_ai_play_time = 0  # 上次AI出牌时间
        self.ai_playing = False  # AI是否正在出牌
    
    @property
    def player(self) -> Entity:
        """获取玩家主角色（简化为第一个实体）"""
        return self.player_team[0] if self.player_team else None
    
    @property
    def enemy(self) -> Entity:
        """获取敌人主角色（简化为第一个实体）"""
        return self.enemy_team[0] if self.enemy_team else None
    
    @property
    def current_entity(self) -> Optional[Entity]:
        """获取当前行动的实体"""
        if self.all_entities and 0 <= self.current_entity_index < len(self.all_entities):
            return self.all_entities[self.current_entity_index]
        return None
    
    def start_battle(self):
        """开始战斗"""
        self.battle_log.add("战斗开始！")
        self.current_round = 0
        self.battle_finished = False
        
        # 锁定所有实体的装备（战斗中不能更换）
        for entity in self.player_team + self.enemy_team:
            if hasattr(entity, 'equipment_manager'):
                entity.equipment_manager.in_combat = True
        
        # 构建行动顺序列表（所有队友和敌人交替行动）
        self._build_action_order()
        
        self.begin_round()
    
    def _build_action_order(self):
        """构建行动顺序列表"""
        # 简单实现：先所有队友，再所有敌人
        # 可以根据速度属性等调整顺序
        self.all_entities = list(self.player_team) + list(self.enemy_team)
        self.current_entity_index = 0
    
    def begin_round(self):
        """开始新回合"""
        self.current_round += 1
        self.battle_log.add(f"\n=== 第 {self.current_round} 回合 ===")
        
        # 重置AP和MD
        for entity in self.player_team + self.enemy_team:
            entity.ap = entity.max_ap
            entity.md = entity.max_md
        
        # 抽牌（第1回合已经在reset_for_battle中抽过初始手牌了）
        if self.current_round > 1:
            for entity in self.player_team + self.enemy_team:
                old_hand_size = len(entity.hand)
                entity.draw_hand()
                new_hand_size = len(entity.hand)
                # 显示实际抽取的卡牌数量（新抽的）
                drawn_count = new_hand_size - old_hand_size
                if drawn_count > 0:
                    self.battle_log.add(f"{entity.name}抽牌: {old_hand_size} -> {new_hand_size}张 (抽{drawn_count}张)", level=2)
                else:
                    self.battle_log.add(f"{entity.name}手牌: {old_hand_size} -> {new_hand_size}张", level=2)
        
        # 装备提供格挡
        for entity in self.player_team + self.enemy_team:
            armor = entity.equipment.get("armor")
            if armor:
                # 使用新的骰子格挡系统
                if hasattr(armor, 'block_dice') and armor.block_dice:
                    block_amount = armor.roll_block()
                    entity.add_block(block_amount)
                elif hasattr(armor, 'block_value') and armor.block_value > 0:
                    # 兼容旧系统
                    entity.add_block(armor.block_value)
                
                # 每回合再生的格挡值（圆盾效果）
                if hasattr(armor, 'block_per_turn') and armor.block_per_turn > 0:
                    regen_block = armor.block_per_turn
                    entity.add_block(regen_block)
        
        # 处理Buff效果
        self._process_all_buffs()
        
        # 重置行动索引
        self.current_entity_index = 0
        
        # 清除所有拖动状态（防止引用已不存在的卡牌）
        if hasattr(self, 'card_view') and self.card_view:
            self.card_view.input_handler.clear_drag_states()
        
        # 检查第一个实体是否是玩家控制
        if self.all_entities:
            first_entity = self.all_entities[0]
            self.is_player_turn = (first_entity.control_type == ControlType.PLAYER)
            
            # 如果第一个是AI，启动AI回合
            if not self.is_player_turn:
                self._start_ai_turn()
    
    def _process_all_buffs(self):
        """处理所有实体的Buff"""
        for entity in self.player_team + self.enemy_team:
            effects = entity.process_buffs()
            for effect in effects:
                self.battle_log.add(effect)
    
    def play_card(self, card: Card, target: Entity) -> tuple:
        """玩家打出卡牌
        
        Returns:
            tuple: (success: bool, is_permanent: bool)
        """
        current = self.current_entity
        if not current or not self.is_player_turn or self.battle_finished:
            return False, False, []
        
        if current.control_type != ControlType.PLAYER:
            return False, False, []
        
        success, is_permanent, log_entries = current.play_card(card, target)
        if success:
            # 将日志条目添加到战斗日志
            for entry in log_entries:
                if isinstance(entry, tuple):
                    # 新格式: (message, level, color_key)
                    message, level, color_key = entry
                    self.battle_log.add(message, level=level, color_key=color_key)
                else:
                    # 旧格式: 字符串
                    self.battle_log.add(entry, level=0)
            
            # 检查战斗是否结束
            self._check_battle_end()
            return True, is_permanent, log_entries
        
        return False, False, []
    
    def end_current_entity_turn(self):
        """结束当前实体的回合"""
        if self.battle_finished:
            return
        
        current = self.current_entity
        if current:
            self.battle_log.add(f"{current.name}回合结束")
        
        # 移动到下一个实体
        self.current_entity_index += 1
        
        # 检查是否所有实体都行动完毕
        if self.current_entity_index >= len(self.all_entities):
            # 开始新回合
            if not self.battle_finished:
                self.begin_round()
        else:
            # 检查下一个实体是否是玩家控制
            next_entity = self.all_entities[self.current_entity_index]
            self.is_player_turn = (next_entity.control_type == ControlType.PLAYER)
            
            # 如果是AI，启动AI回合
            if not self.is_player_turn:
                self._start_ai_turn()
    
    def end_player_turn(self):
        """结束玩家回合（兼容旧接口）"""
        self.end_current_entity_turn()
    
    def _start_ai_turn(self):
        """启动AI回合"""
        if self.battle_finished:
            return
        
        current = self.current_entity
        if not current:
            return
        
        self.ai_playing = True
        self.last_ai_play_time = time.time()
        self.battle_log.add(f"{current.name}回合开始")
        self.battle_log.add(f"{current.name}状态 - AP:{current.ap}/{current.max_ap}, MD:{current.md}/{current.max_md}, 手牌数:{len(current.hand)}", level=2)
        
        # AI抽牌（已经在begin_round中完成）
    
    def update_ai(self):
        """更新AI逻辑（需要在游戏循环中调用）"""
        if not self.ai_playing or self.battle_finished:
            return
        
        current = self.current_entity
        if not current or current.control_type == ControlType.PLAYER:
            return
        
        # 检查是否到了出牌时间
        current_time = time.time()
        if current_time - self.last_ai_play_time < CONSTANTS.AI_CARD_PLAY_INTERVAL:
            return
        
        # AI出牌逻辑
        self._ai_play_card(current)
        self.last_ai_play_time = current_time
    
    def _ai_play_card(self, ai_entity: Entity):
        """AI打出一张卡牌"""
        if self.battle_finished:
            return
        
        # 选择一张能支付的卡牌
        playable_cards = [c for c in ai_entity.hand if c.ap_cost <= ai_entity.ap]
        
        self.battle_log.add(f"{ai_entity.name}检查出牌 - 手牌:{len(ai_entity.hand)}张, AP:{ai_entity.ap}, 可出:{len(playable_cards)}张", level=2)
        
        if not playable_cards:
            # 没有可出的牌，检查是否还有手牌
            if not ai_entity.hand:
                self.battle_log.add(f"{ai_entity.name}手牌为空，结束回合")
            else:
                # 打印所有手牌的AP消耗
                card_info = ", ".join([f"{c.name}({c.ap_cost}AP)" for c in ai_entity.hand])
                self.battle_log.add(f"{ai_entity.name}没有足够AP出牌（AP:{ai_entity.ap}），手牌: [{card_info}]，结束回合")
            # 没有可出的牌，结束回合
            self.ai_playing = False
            self.end_current_entity_turn()
            return
        
        # 简单AI：随机选择一张卡牌
        import random
        card = random.choice(playable_cards)
        self.battle_log.add(f"{ai_entity.name}选择卡牌: {card.name} (AP消耗:{card.ap_cost})", level=2)
        
        # 选择目标（优先攻击敌方存活的实体）
        target = self._choose_ai_target(ai_entity)
        
        if target:
            # 检查是否在卡牌的有效范围内
            distance = self._calculate_distance(ai_entity.position, target.position)
            max_range = self._get_card_range(card)
            
            self.battle_log.add(f"{ai_entity.name}准备出牌 - 目标:{target.name}, 距离:{distance}, 卡牌范围:{max_range}", level=2)
            
            # 如果不在范围内，先尝试移动
            if distance > max_range and ai_entity.md > 0:
                moved = self._ai_move_towards_target(ai_entity, target, max_range)
                
                if not moved:
                    # 无法移动，移除这张卡，但继续尝试其他卡牌
                    ai_entity.hand.remove(card)
                    # 不结束回合，让update_ai下次调用时继续出牌
                    return
                else:
                    # 移动成功，重新检查距离并尝试出牌
                    distance = self._calculate_distance(ai_entity.position, target.position)
                    max_range = self._get_card_range(card)
                    
                    self.battle_log.add(f"{ai_entity.name}移动后检查 - 距离:{distance}, 卡牌范围:{max_range}", level=2)
                    
                    if distance <= max_range:
                        # 移动后在范围内，立即出牌
                        success, _, log_entries = ai_entity.play_card(card, target)
                        if success:
                            # 添加AI卡牌使用日志
                            for entry in log_entries:
                                if isinstance(entry, tuple):
                                    message, level, color_key = entry
                                    self.battle_log.add(message, level=level, color_key=color_key)
                                else:
                                    self.battle_log.add(entry, level=0)
                            self._check_battle_end()
                            # 出牌成功，不结束回合，让AI可以继续出牌
                            return
                        else:
                            # 出牌失败，移除这张卡
                            ai_entity.hand.remove(card)
                            self.battle_log.add(f"{ai_entity.name}出牌失败，移除卡牌", level=2)
                    # 移动后仍然无法出牌，保留卡牌，结束本回合
                    self.ai_playing = False
                    self.end_current_entity_turn()
                    return
            
            # 再次检查距离
            distance = self._calculate_distance(ai_entity.position, target.position)
            max_range = self._get_card_range(card)
            
            if distance <= max_range:
                # 打出卡牌
                success, _, log_entries = ai_entity.play_card(card, target)
                if success:
                    # 添加AI卡牌使用日志
                    for entry in log_entries:
                        if isinstance(entry, tuple):
                            message, level, color_key = entry
                            self.battle_log.add(message, level=level, color_key=color_key)
                        else:
                            self.battle_log.add(entry, level=0)
                    self._check_battle_end()
                    # 出牌成功，不结束回合，让AI可以继续出牌
                    return
                else:
                    # 出牌失败，移除这张卡，继续尝试其他卡牌
                    ai_entity.hand.remove(card)
                    return
            else:
                # 仍然不在范围内，保留卡牌到下回合，结束回合
                self.ai_playing = False
                self.end_current_entity_turn()
        else:
            # 没有目标，移除这张卡，但继续尝试其他卡牌
            ai_entity.hand.remove(card)
            # 不结束回合，让update_ai下次调用时继续出牌
    
    def _choose_ai_target(self, ai_entity: Entity) -> Optional[Entity]:
        """AI选择目标 - 优先选择最近的敌方单位"""
        # 判断AI属于哪一方
        is_player_side = ai_entity in self.player_team
        
        # 选择对立方的存活实体
        if is_player_side:
            # AI队友的目标：所有敌人
            targets = [e for e in self.enemy_team if e.is_alive()]
        else:
            # 敌人的目标：玩家队伍的所有成员（包括玩家和队友）
            targets = [e for e in self.player_team if e.is_alive()]
        
        if not targets:
            return None
        
        # 选择距离最近的目标
        closest_target = None
        min_distance = float('inf')
        
        for target in targets:
            distance = self._calculate_distance(ai_entity.position, target.position)
            if distance < min_distance:
                min_distance = distance
                closest_target = target
        
        return closest_target
    
    def _calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """计算两个位置之间的曼哈顿距离"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _get_card_range(self, card: Card) -> int:
        """根据卡牌类型获取有效距离"""
        # 如果有atk_dis属性，使用它
        if hasattr(card, 'atk_dis') and card.atk_dis:
            return card.atk_dis
        
        # 否则根据卡牌类型返回默认值
        default_range = 3
        
        if card.card_type.value in ["atk_phy", "atk_mag"]:
            return 5
        elif card.card_type.value == "blk":
            return 0
        elif card.card_type.value == "hel":
            return 3
        else:
            return default_range
    
    def _ai_move_towards_target(self, ai_entity: Entity, target: Entity, required_range: int) -> bool:
        """
        AI尝试向目标移动，直到进入卡牌范围
        
        Args:
            ai_entity: AI实体
            target: 目标实体
            required_range: 需要的距离范围
        
        Returns:
            是否成功移动
        """
        # 使用真实的地图，如果没有则创建临时地图
        tile_map = self.tile_map
        if not tile_map:
            from tile_map import TileMap
            tile_map = TileMap(width=20, height=15)
        
        current_distance = self._calculate_distance(ai_entity.position, target.position)
        
        # 如果已经在范围内，不需要移动
        if current_distance <= required_range:
            return True
        
        # 获取所有其他实体的位置
        all_entities = self.player_team + self.enemy_team
        other_positions = [e.position for e in all_entities if e != ai_entity and e.is_alive()]
        
        # 尝试找到一个合适的位置（在required_range内且MD足够）
        best_position = None
        min_md_cost = float('inf')
        
        # 搜索目标周围的位置
        for dy in range(-required_range, required_range + 1):
            for dx in range(-required_range, required_range + 1):
                test_x = target.position[0] + dx
                test_y = target.position[1] + dy
                
                # 检查边界
                if test_x < 0 or test_x >= tile_map.width or test_y < 0 or test_y >= tile_map.height:
                    continue
                
                # 检查距离是否在范围内
                distance = abs(dx) + abs(dy)
                if distance > required_range or distance == 0:
                    continue
                
                # 检查是否有其他实体
                if (test_x, test_y) in other_positions:
                    continue
                
                # 尝试找路径
                path = tile_map.find_path_astar(ai_entity.position, (test_x, test_y), other_positions)
                if path:
                    # 计算MD消耗
                    md_cost = tile_map.calculate_path_md_cost(path, other_positions)
                    
                    # 检查MD是否足够，并选择消耗最小的位置
                    if md_cost <= ai_entity.md and md_cost < min_md_cost:
                        min_md_cost = md_cost
                        best_position = (test_x, test_y)
        
        # 如果找到了合适的位置，执行移动
        if best_position:
            success = self.move_entity(ai_entity, best_position, tile_map)
            if success:
                self.battle_log.add(f"{ai_entity.name}移动到({best_position[0]}, {best_position[1]})以接近目标")
                return True
        else:
            # 如果没有找到范围内的位置，尝试尽可能靠近
            # 找一个最近的可达位置
            closest_pos = None
            closest_dist = float('inf')
            
            for y in range(tile_map.height):
                for x in range(tile_map.width):
                    if (x, y) in other_positions:
                        continue
                    
                    tile = tile_map.get_tile(x, y)
                    if not tile or not tile.is_walkable:
                        continue
                    
                    path = tile_map.find_path_astar(ai_entity.position, (x, y), other_positions)
                    if path:
                        md_cost = tile_map.calculate_path_md_cost(path, other_positions)
                        if md_cost <= ai_entity.md:
                            dist_to_target = self._calculate_distance((x, y), target.position)
                            if dist_to_target < closest_dist:
                                closest_dist = dist_to_target
                                closest_pos = (x, y)
            
            if closest_pos:
                success = self.move_entity(ai_entity, closest_pos, tile_map)
                if success:
                    self.battle_log.add(f"{ai_entity.name}移动到({closest_pos[0]}, {closest_pos[1]})以接近目标")
                    return True
        
        return False
    
    def _enemy_turn(self):
        """敌人回合（旧版兼容，已废弃）"""
        pass
    
    def _check_battle_end(self):
        """检查战斗是否结束"""
        # 检查玩家队伍
        player_alive = any(entity.is_alive() for entity in self.player_team)
        enemy_alive = any(entity.is_alive() for entity in self.enemy_team)
        
        if not player_alive:
            self.battle_finished = True
            self.winner = self.enemy_team
            self.battle_log.add("\n战斗结束！敌人获胜！")
            
            # 解锁所有实体的装备
            for entity in self.player_team + self.enemy_team:
                if hasattr(entity, 'equipment_manager'):
                    entity.equipment_manager.in_combat = False
                    
        elif not enemy_alive:
            self.battle_finished = True
            self.winner = self.player_team
            self.battle_log.add(f"\n战斗结束！{self.player.name}获胜！")
            
            # 解锁所有实体的装备
            for entity in self.player_team + self.enemy_team:
                if hasattr(entity, 'equipment_manager'):
                    entity.equipment_manager.in_combat = False
    
    def skip_turn(self):
        """跳过当前回合"""
        if self.is_player_turn and not self.battle_finished:
            current = self.current_entity
            if current:
                self.battle_log.add(f"{current.name}跳过回合")
            self.end_current_entity_turn()
    
    def move_entity(self, entity: Entity, target_position: Tuple[int, int], tile_map) -> bool:
        """
        移动实体到目标位置
        
        Args:
            entity: 要移动的实体
            target_position: 目标位置 (x, y)
            tile_map: 瓦片地图对象
        
        Returns:
            是否移动成功
        """
        if not entity or entity.md <= 0:
            return False
        
        # 获取所有其他实体的位置
        all_entities = self.player_team + self.enemy_team
        other_positions = [e.position for e in all_entities if e != entity and e.is_alive()]
        
        # 检查目标位置是否有其他实体
        is_ally_target = False
        if target_position in other_positions:
            # 检查是否是队友
            for e in all_entities:
                if e.position == target_position and e.is_alive() and e != entity:
                    # 判断是否是队友（同阵营）
                    is_same_team = (entity in self.player_team and e in self.player_team) or \
                                  (entity in self.enemy_team and e in self.enemy_team)
                    if is_same_team:
                        is_ally_target = True
                    else:
                        # 敌人位置，不能移动
                        return False
                    break
        
        # 使用A*算法找路径
        path = tile_map.find_path_astar(entity.position, target_position, other_positions, is_ally_target)
        
        if not path:
            self.battle_log.add(f"{entity.name}无法到达目标位置")
            return False
        
        # 计算MD消耗
        md_cost = tile_map.calculate_path_md_cost(path, other_positions, is_ally_target)
        
        # 检查MD是否足够
        if entity.md < md_cost:
            self.battle_log.add(f"{entity.name}MD不足！需要{md_cost}，剩余{entity.md}")
            return False
        
        # 执行移动
        entity.position = target_position
        entity.md -= md_cost
        
        self.battle_log.add(f"{entity.name}移动到 ({target_position[0]}, {target_position[1]})，消耗{md_cost}MD")
        return True
    
    def get_battle_status(self) -> dict:
        """获取战斗状态信息"""
        status = {
            "round": self.current_round,
            "is_player_turn": self.is_player_turn,
            "battle_finished": self.battle_finished,
            "winner": self.winner[0].name if self.winner else None,
            "current_entity": self.current_entity.name if self.current_entity else None,
            "entities": []
        }
        
        # 添加所有实体的状态
        for entity in self.player_team + self.enemy_team:
            status["entities"].append({
                "name": entity.name,
                "hp": entity.hp,
                "max_hp": entity.max_hp,
                "block": entity.block,
                "ap": entity.ap,
                "max_ap": entity.max_ap,
                "md": entity.md,
                "max_md": entity.max_md,
                "control_type": entity.control_type.value,
                "position": entity.position,
                "is_alive": entity.is_alive()
            })
        
        # 为了兼容性，仍然保留player和enemy字段
        if self.player:
            status.update({
                "player_hp": self.player.hp,
                "player_max_hp": self.player.max_hp,
                "player_block": self.player.block,
                "player_ap": self.player.ap,
                "player_max_ap": self.player.max_ap,
            })
        
        if self.enemy:
            status.update({
                "enemy_hp": self.enemy.hp,
                "enemy_max_hp": self.enemy.max_hp,
                "enemy_block": self.enemy.block,
                "enemy_ap": self.enemy.ap,
                "enemy_max_ap": self.enemy.max_ap,
            })
        
        return status
    
    def __str__(self):
        status = self.get_battle_status()
        return (
            f"Round: {status['round']}\n"
            f"Player: {status['player_hp']}/{status['player_max_hp']} HP, "
            f"{status['player_block']} Block, {status['player_ap']} AP\n"
            f"Enemy: {status['enemy_hp']}/{status['enemy_max_hp']} HP, "
            f"{status['enemy_block']} Block, {status['enemy_ap']} AP\n"
            f"Turn: {'Player' if status['is_player_turn'] else 'Enemy'}\n"
            f"Finished: {status['battle_finished']}"
        )

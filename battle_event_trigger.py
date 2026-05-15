"""
战斗事件触发器模块
处理地图节点上的战斗触发逻辑
"""
from typing import List, Optional, Tuple, Callable
from map_system import MapNode, NodeType
from models import Entity


class BattleEventTrigger:
    """战斗事件触发器 - 管理地图节点的战斗触发"""
    
    def __init__(self, map_system, battle_callback: Callable = None):
        """
        初始化战斗事件触发器
        
        Args:
            map_system: 地图系统实例
            battle_callback: 战斗开始回调函数，接收 (player_team, enemy_team, node) 参数
        """
        self.map_system = map_system
        self.battle_callback = battle_callback
        self.last_battle_node: Optional[MapNode] = None
    
    def can_trigger_battle(self, node: MapNode) -> bool:
        """
        检查是否可以在此节点触发战斗
        
        Args:
            node: 目标节点
            
        Returns:
            是否可以触发战斗
        """
        # 必须是战斗区节点
        if node.node_type != NodeType.BATTLE_ZONE:
            return False
        
        # 如果已经清剿，不再触发战斗（或降低触发概率）
        if node.is_cleared:
            print(f"[战斗触发] 节点 {node.name} 已被清剿，跳过战斗")
            return False
        
        # 检查是否已访问过（可选：可以允许重复战斗）
        # if node.is_visited:
        #     return False
        
        return True
    
    def trigger_battle(self, node: MapNode, player_entity: Entity) -> Tuple[bool, str]:
        """
        在指定节点触发战斗
        
        Args:
            node: 战斗节点
            player_entity: 玩家实体
            
        Returns:
            (是否成功触发, 消息)
        """
        if not self.can_trigger_battle(node):
            return False, f"无法在 {node.name} 触发战斗"
        
        print(f"\n[战斗触发] 在 {node.name} 触发战斗！")
        print(f"[战斗触发] 节点标签: {', '.join(node.tags)}")
        
        # 根据节点标签生成敌人
        enemy_team = self._generate_enemies_from_tags(node, player_entity)
        
        if not enemy_team:
            return False, "未能生成敌人"
        
        # 记录最后战斗的节点
        self.last_battle_node = node
        
        # 调用战斗回调
        if self.battle_callback:
            try:
                player_team = [player_entity]
                self.battle_callback(player_team, enemy_team, node)
                return True, f"进入 {node.name} 的战斗！"
            except Exception as e:
                return False, f"战斗触发失败: {str(e)}"
        else:
            return False, "未设置战斗回调函数"
    
    def _generate_enemies_from_tags(self, node: MapNode, player_entity: Entity) -> List[Entity]:
        """
        根据节点标签生成敌人队伍
        
        Args:
            node: 战斗节点
            player_entity: 玩家实体（用于平衡难度）
            
        Returns:
            敌人生成的实体列表
        """
        enemies = []
        tags = [tag.lower() for tag in node.tags]
        
        # 根据标签确定敌人数和类型
        enemy_count = 1
        enemy_career = None
        
        if "危险" in tags or "洞穴" in tags:
            enemy_count = 2
            enemy_career = "战士"  # 更强的敌人
        elif "废墟" in tags:
            enemy_count = 1
            enemy_career = "流浪者"
        elif "宝藏" in tags:
            enemy_count = 1
            enemy_career = "行商"  # 可能有特殊卡牌
        else:
            enemy_count = 1
            enemy_career = "农民"  # 默认敌人
        
        # 生成敌人
        for i in range(enemy_count):
            enemy = self._create_enemy(f"敌人_{i+1}", enemy_career, player_entity.level)
            if enemy:
                # 为敌人设置位置（距离玩家8-14格）
                spawn_pos = self._generate_enemy_spawn_position(player_entity)
                if spawn_pos:
                    enemy.position = spawn_pos
                    print(f"[战斗触发] 设置敌人位置: {spawn_pos}")
                enemies.append(enemy)
        
        print(f"[战斗触发] 生成了 {len(enemies)} 个敌人")
        return enemies
    
    def _generate_enemy_spawn_position(self, player_entity: Entity, min_distance: int = 8, max_distance: int = 14) -> Optional[Tuple[int, int]]:
        """
        生成敌人生成位置（距离玩家8-14格的随机非障碍物位置）
        
        Args:
            player_entity: 玩家实体
            min_distance: 最小距离（曼哈顿距离）
            max_distance: 最大距离（曼哈顿距离）
            
        Returns:
            生成位置坐标，失败返回None
        """
        import random
        from tile_map import TileMap
        
        # 获取tile_map（如果存在）
        tile_map = None
        if hasattr(self, 'map_system') and self.map_system:
            # 尝试从map_system获取tile_map
            if hasattr(self.map_system, 'tile_map'):
                tile_map = self.map_system.tile_map
        
        # 如果没有tile_map，创建一个默认的
        if not tile_map:
            tile_map = TileMap(width=20, height=15)
        
        player_pos = player_entity.position
        if not player_pos:
            player_pos = (10, 7)  # 默认玩家位置
        
        # 收集所有符合条件的位置
        valid_positions = []
        
        for y in range(tile_map.height):
            for x in range(tile_map.width):
                # 计算曼哈顿距离
                distance = abs(x - player_pos[0]) + abs(y - player_pos[1])
                
                # 检查距离是否在范围内
                if min_distance <= distance <= max_distance:
                    # 检查是否为非障碍物
                    tile = tile_map.get_tile(x, y)
                    if tile and tile.is_walkable:
                        valid_positions.append((x, y))
        
        # 随机选择一个位置
        if valid_positions:
            return random.choice(valid_positions)
        else:
            # 如果没有合适的位置，返回一个默认位置（玩家右侧10格）
            default_x = min(player_pos[0] + 10, tile_map.width - 1)
            default_y = player_pos[1]
            return (default_x, default_y)
    
    def _create_enemy(self, name: str, career_name: str, level: int = 1) -> Optional[Entity]:
        """
        创建敌人实体
        
        Args:
            name: 敌人名称
            career_name: 职业名称
            level: 等级
            
        Returns:
            敌人实体，失败返回None
        """
        try:
            from models import ControlType
            from career_system import CareerFactory, CareerType
            from card_database import get_career_deck
            
            # 根据职业设置基础属性
            career_stats = {
                "战士": {"hp": 30, "ap": 3, "mp": 5, "career_type": CareerType.FARMER},
                "流浪者": {"hp": 25, "ap": 4, "mp": 6, "career_type": CareerType.DRIFTER},
                "行商": {"hp": 20, "ap": 3, "mp": 8, "career_type": CareerType.PEDLAR},
                "农民": {"hp": 22, "ap": 3, "mp": 5, "career_type": CareerType.FARMER},
                "手艺人": {"hp": 24, "ap": 3, "mp": 7, "career_type": CareerType.ARTISAN},
                "学者": {"hp": 18, "ap": 2, "mp": 10, "career_type": CareerType.SCHOLAR}
            }
            
            stats = career_stats.get(career_name, {"hp": 20, "ap": 3, "mp": 5, "career_type": CareerType.FARMER})
            career_type = stats["career_type"]
            
            # 获取职业专属卡组
            deck = get_career_deck(career_type)
            
            # 获取职业对象
            career = CareerFactory.get_career(career_type)
            
            # 创建敌人
            enemy = Entity(
                name=f"{name}_{career_name}",
                max_hp=stats["hp"] + (level - 1) * 5,
                max_ap=stats["ap"],
                equipment={},
                cards=deck,
                hand_size=7,  # 手牌上限7张（不含常驻牌）
                control_type=ControlType.AI
            )
            enemy.level = level
            enemy.mp = stats["mp"]
            enemy.max_mp = stats["mp"]
            
            # 设置职业
            if career:
                enemy.set_career(career)
            
            print(f"[战斗触发] 创建了 {enemy.name} (HP: {enemy.max_hp}, AP: {enemy.ap}, 卡组: {len(deck)}张牌)")
            return enemy
            
        except Exception as e:
            print(f"[战斗触发] 创建敌人失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def on_battle_complete(self, won: bool):
        """
        战斗完成后的处理
        
        Args:
            won: 是否胜利
        """
        if won and self.last_battle_node:
            # 标记节点为已清剿
            self.map_system.clear_node(self.last_battle_node.node_id)
            print(f"[战斗触发] 战斗胜利！节点 {self.last_battle_node.name} 已标记为清剿")
            
            # 保存地图状态
            self.map_system.save_to_file("save.json")
        else:
            print(f"[战斗触发] 战斗失败或未胜利")
        
        self.last_battle_node = None


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("战斗事件触发器测试")
    print("=" * 70)
    
    from map_system import MapSystem
    
    # 创建地图系统
    map_system = MapSystem()
    map_system.create_example_map()
    
    # 创建触发器
    def dummy_battle_callback(player_team, enemy_team, node):
        print(f"  → 模拟战斗: {len(player_team)} vs {len(enemy_team)} 在 {node.name}")
    
    trigger = BattleEventTrigger(map_system, dummy_battle_callback)
    
    # 测试1: 检查战斗节点
    print("\n测试1: 检查各个节点的战斗触发条件")
    for node in map_system.get_all_nodes():
        can_trigger = trigger.can_trigger_battle(node)
        status = "✓ 可触发" if can_trigger else "✗ 不可触发"
        print(f"  {node.name} ({node.node_type.value}): {status}")
    
    # 测试2: 尝试触发战斗
    print("\n测试2: 触发战斗节点")
    test_node = map_system.nodes.get("ruins_001")
    if test_node:
        # 创建一个测试玩家
        from models import ControlType
        player = Entity(
            name="测试玩家",
            max_hp=50,
            max_ap=3,
            equipment={},
            cards=[],
            control_type=ControlType.PLAYER
        )
        player.level = 1
        
        success, message = trigger.trigger_battle(test_node, player)
        print(f"  结果: {message}")
        
        # 模拟战斗胜利
        if success:
            print("\n测试3: 手动标记节点为清剿（模拟战斗胜利）")
            # 注意：在实际游戏中，这应该在战斗结束后由战斗系统调用
            # 这里只是为了测试清剿功能
            map_system.clear_node(test_node.node_id)
            
            # 再次检查是否可以触发
            can_trigger_again = trigger.can_trigger_battle(test_node)
            print(f"  清剿后能否再次触发: {'是' if can_trigger_again else '否'}")
            print(f"  节点is_cleared状态: {test_node.is_cleared}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70 + "\n")

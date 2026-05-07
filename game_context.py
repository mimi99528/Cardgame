"""
游戏上下文模块
提供统一的游戏状态传递对象，解耦各模块之间的直接依赖
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class SceneType(Enum):
    """场景类型枚举"""
    COMBAT = "combat"           # 战斗场景
    EXPLORATION = "exploration" # 探索场景
    SOCIAL = "social"           # 社交场景
    MAP = "map"                 # 大地图场景
    CAMP = "camp"               # 营地场景
    NARRATIVE = "narrative"     # 叙事场景


@dataclass
class GameContext:
    """
    游戏上下文对象
    封装当前游戏状态，传递给卡牌效果执行器、事件处理器等
    避免各模块直接依赖具体实现类（如 BattleSystem、TileMap）
    """
    # 当前场景类型
    scene_type: SceneType = SceneType.COMBAT
    
    # 当前行动的实体（玩家或 AI）
    current_actor: Any = None
    
    # 当前可用的目标列表（根据场景类型可能是敌人、友军、NPC 等）
    targets: List[Any] = field(default_factory=list)
    
    # 所有友军列表（用于群体 buff、治疗等）
    allies: List[Any] = field(default_factory=list)
    
    # 所有敌人列表（用于 AOE 攻击等）
    enemies: List[Any] = field(default_factory=list)
    
    # 瓦片地图引用（探索、移动相关效果需要）
    tile_map: Any = None
    
    # 战斗系统引用（仅在战斗场景有效）
    battle: Any = None
    
    # 事件总线引用
    event_bus: Any = None
    
    # 骰子系统引用
    dice_system: Any = None
    
    # 卡牌数据库引用
    card_database: Dict[str, Any] = field(default_factory=dict)
    
    # 额外上下文数据（用于扩展）
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    # 日志记录器（可选）
    battle_log: Any = None
    
    @property
    def is_combat(self) -> bool:
        """判断是否在战斗场景"""
        return self.scene_type == SceneType.COMBAT
    
    @property
    def is_exploration(self) -> bool:
        """判断是否在探索场景"""
        return self.scene_type == SceneType.EXPLORATION
    
    @property
    def is_social(self) -> bool:
        """判断是否在社交场景"""
        return self.scene_type == SceneType.SOCIAL
    
    def get_target_by_name(self, name: str) -> Optional[Any]:
        """根据名称获取目标"""
        for target in self.targets:
            if hasattr(target, 'name') and target.name == name:
                return target
        return None
    
    def get_enemies(self) -> List[Any]:
        """获取所有敌人"""
        return self.enemies
    
    def get_allies(self) -> List[Any]:
        """获取所有友军"""
        return self.allies
    
    def set_extra(self, key: str, value: Any):
        """设置额外数据"""
        self.extra_data[key] = value
    
    def get_extra(self, key: str, default=None) -> Any:
        """获取额外数据"""
        return self.extra_data.get(key, default)
    
    def copy(self) -> 'GameContext':
        """创建上下文的浅拷贝"""
        from copy import deepcopy
        return GameContext(
            scene_type=self.scene_type,
            current_actor=self.current_actor,
            targets=self.targets[:],
            allies=self.allies[:],
            enemies=self.enemies[:],
            tile_map=self.tile_map,
            battle=self.battle,
            event_bus=self.event_bus,
            dice_system=self.dice_system,
            card_database=self.card_database,
            extra_data=deepcopy(self.extra_data),
            battle_log=self.battle_log
        )
    
    def with_current_actor(self, actor: Any) -> 'GameContext':
        """返回一个设置了当前行动者的新上下文"""
        new_ctx = self.copy()
        new_ctx.current_actor = actor
        return new_ctx
    
    def with_targets(self, targets: List[Any]) -> 'GameContext':
        """返回一个设置了目标列表的新上下文"""
        new_ctx = self.copy()
        new_ctx.targets = targets
        return new_ctx


# ==================== 便捷工厂函数 ====================

def create_combat_context(
    player_team: List[Any],
    enemy_team: List[Any],
    battle_system: Any,
    tile_map: Any = None,
    event_bus: Any = None,
    dice_system: Any = None,
    battle_log: Any = None
) -> GameContext:
    """
    创建战斗场景的上下文
    
    Args:
        player_team: 玩家队伍列表
        enemy_team: 敌人队伍列表
        battle_system: 战斗系统实例
        tile_map: 瓦片地图实例（可选）
        event_bus: 事件总线实例（可选）
        dice_system: 骰子系统实例（可选）
        battle_log: 战斗日志实例（可选）
    
    Returns:
        配置好的战斗场景上下文
    """
    ctx = GameContext(
        scene_type=SceneType.COMBAT,
        current_actor=player_team[0] if player_team else None,
        targets=enemy_team[:],
        allies=player_team[:],
        enemies=enemy_team[:],
        tile_map=tile_map,
        battle=battle_system,
        event_bus=event_bus,
        dice_system=dice_system,
        battle_log=battle_log
    )
    return ctx


def create_exploration_context(
    player: Any,
    tile_map: Any,
    npcs: List[Any] = None,
    event_bus: Any = None,
    dice_system: Any = None
) -> GameContext:
    """
    创建探索场景的上下文
    
    Args:
        player: 玩家实体
        tile_map: 瓦片地图实例
        npcs: NPC 列表（可选）
        event_bus: 事件总线实例（可选）
        dice_system: 骰子系统实例（可选）
    
    Returns:
        配置好的探索场景上下文
    """
    ctx = GameContext(
        scene_type=SceneType.EXPLORATION,
        current_actor=player,
        targets=npcs or [],
        allies=[player],
        enemies=[],
        tile_map=tile_map,
        event_bus=event_bus,
        dice_system=dice_system
    )
    return ctx


def create_social_context(
    player: Any,
    npc: Any,
    event_bus: Any = None,
    dice_system: Any = None
) -> GameContext:
    """
    创建社交场景的上下文
    
    Args:
        player: 玩家实体
        npc: NPC 实体
        event_bus: 事件总线实例（可选）
        dice_system: 骰子系统实例（可选）
    
    Returns:
        配置好的社交场景上下文
    """
    ctx = GameContext(
        scene_type=SceneType.SOCIAL,
        current_actor=player,
        targets=[npc],
        allies=[player],
        enemies=[],
        event_bus=event_bus,
        dice_system=dice_system
    )
    return ctx

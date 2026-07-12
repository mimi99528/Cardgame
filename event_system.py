"""
游戏事件系统模块
提供基于事件通知的架构，支持伤害结算、治疗等关键节点的拦截和修改
"""
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass, field


class GameEventType(Enum):
    """游戏事件类型枚举"""
    # 卡牌相关事件
    CARD_PLAY_BEFORE = "card_play_before"      # 卡牌打出前
    CARD_PLAY_AFTER = "card_play_after"        # 卡牌打出后
    
    # 伤害相关事件
    DAMAGE_CALCULATE = "damage_calculate"      # 伤害计算时（可修改）
    DAMAGE_BEFORE_APPLY = "damage_before_apply"  # 伤害应用前
    DAMAGE_AFTER_APPLY = "damage_after_apply"    # 伤害应用后
    
    # 治疗相关事件
    HEAL_CALCULATE = "heal_calculate"          # 治疗量计算时（可修改）
    HEAL_BEFORE_APPLY = "heal_before_apply"    # 治疗应用前
    HEAL_AFTER_APPLY = "heal_after_apply"      # 治疗应用后
    
    # 格挡相关事件
    BLOCK_CALCULATE = "block_calculate"        # 格挡值计算时
    BLOCK_BEFORE_APPLY = "block_before_apply"  # 格挡应用前
    
    # Buff相关事件
    BUFF_APPLY = "buff_apply"                  # Buff应用时
    BUFF_REMOVE = "buff_remove"                # Buff移除时
    
    # 回合相关事件
    TURN_START = "turn_start"                  # 回合开始（所有实体）
    TURN_END = "turn_end"                      # 回合结束（所有实体行动完毕）
    ENTITY_TURN_END = "entity_turn_end"        # 实体回合结束（单个实体行动完毕）
    
    # 移动相关事件
    MOVE_BEFORE = "move_before"                # 移动前
    MOVE_AFTER = "move_after"                  # 移动后
    
    # 装备相关事件
    EQUIP_BEFORE = "equip_before"              # 装备前
    EQUIP_AFTER = "equip_after"                # 装备后
    UNEQUIP_BEFORE = "unequip_before"          # 卸下前
    UNEQUIP_AFTER = "unequip_after"            # 卸下后
    
    # 职业相关事件
    HAND_SIZE_CALCULATE = "hand_size_calculate"  # 手牌上限计算
    SOCIAL_CHECK_BEFORE = "social_check_before"  # 社交检定前
    ENCOUNTER_START = "encounter_start"          # 遭遇开始
    NODE_TRAVEL = "node_travel"                  # 节点移动
    
    # 执念相关事件
    BATTLE_VICTORY = "battle_victory"            # 战斗胜利
    ENEMY_DEFEATED = "enemy_defeated"            # 击败敌人
    LOCATION_VISITED = "location_visited"        # 访问地点
    ITEM_COLLECTED = "item_collected"            # 收集物品
    SOCIAL_CHECK_COMPLETED = "social_check_completed"  # 社交检定完成
    INTELLECT_CHECK_COMPLETED = "intellect_check_completed"  # 心智检定完成
    PROTECTION_ACTION = "protection_action"      # 守护行为
    NPC_HELPED = "npc_helped"                    # 帮助NPC
    QUEST_COMPLETED = "quest_completed"          # 任务完成
    LEVEL_UP = "level_up"                        # 等级提升


@dataclass
class GameEvent:
    """游戏事件对象"""
    event_type: GameEventType
    source: Any  # 事件来源（如卡牌、实体等）
    target: Any  # 事件目标
    data: Dict[str, Any] = field(default_factory=dict)  # 事件数据
    
    def get_value(self, key: str, default=None) -> Any:
        """获取事件数据中的值"""
        return self.data.get(key, default)
    
    def set_value(self, key: str, value: Any):
        """设置事件数据中的值"""
        self.data[key] = value
    
    def has_value(self, key: str) -> bool:
        """检查事件数据中是否有某个值"""
        return key in self.data


class EventHandler:
    """事件处理器"""
    
    def __init__(self, callback: Callable[[GameEvent], None], priority: int = 0):
        self.callback = callback
        self.priority = priority  # 优先级，数值越大越先执行
    
    def __call__(self, event: GameEvent):
        self.callback(event)
    
    def __lt__(self, other):
        return self.priority > other.priority  # 优先级高的排在前面


class EventBus:
    """事件总线 - 管理所有事件的注册和触发"""
    
    def __init__(self):
        self._handlers: Dict[GameEventType, List[EventHandler]] = {}
    
    def register(self, event_type: GameEventType, handler: Callable[[GameEvent], None], priority: int = 0):
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数，接收GameEvent参数
            priority: 优先级（数值越大越先执行）
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(EventHandler(handler, priority))
        # 按优先级排序
        self._handlers[event_type].sort()
    
    def unregister(self, event_type: GameEventType, handler: Callable[[GameEvent], None]):
        """注销事件处理器"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] 
                if h.callback != handler
            ]
    
    def trigger(self, event: GameEvent):
        """
        触发事件
        
        Args:
            event: 游戏事件对象
        """
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                handler(event)
    
    def clear(self):
        """清空所有事件处理器"""
        self._handlers.clear()
    
    def get_handler_count(self, event_type: GameEventType) -> int:
        """获取某类型事件的处理器数量"""
        return len(self._handlers.get(event_type, []))


# 全局事件总线实例
global_event_bus = EventBus()


def get_global_event_bus() -> EventBus:
    """获取全局事件总线"""
    return global_event_bus


# ==================== 便捷函数 ====================

def trigger_event(event_type: GameEventType, source: Any, target: Any, data: Dict[str, Any] = None):
    """
    便捷函数：触发事件
    
    Args:
        event_type: 事件类型
        source: 事件来源
        target: 事件目标
        data: 事件数据
    """
    event = GameEvent(
        event_type=event_type,
        source=source,
        target=target,
        data=data or {}
    )
    global_event_bus.trigger(event)
    return event


def register_event_handler(event_type: GameEventType, handler: Callable[[GameEvent], None], priority: int = 0):
    """
    便捷函数：注册事件处理器
    
    Args:
        event_type: 事件类型
        handler: 处理函数
        priority: 优先级
    """
    global_event_bus.register(event_type, handler, priority)


# ==================== 示例：破盾效果实现 ====================

class BreakShieldModifier:
    """破盾修饰器 - 用于标记伤害应该双倍消耗格挡"""
    
    def __init__(self):
        self.active = False
    
    def activate(self):
        """激活破盾效果"""
        self.active = True
    
    def deactivate(self):
        """停用破盾效果"""
        self.active = False
    
    def is_active(self) -> bool:
        """检查是否激活"""
        return self.active


# 创建全局破盾修饰器实例
break_shield_modifier = BreakShieldModifier()


def setup_break_shield_system():
    """设置破盾系统 - 注册事件处理器"""
    
    def on_damage_calculate(event: GameEvent):
        """伤害计算时，如果破盾激活，则标记双倍格挡消耗"""
        if break_shield_modifier.is_active():
            event.set_value("double_block_damage", True)
            print(f"[事件] 破盾效果激活：下次伤害将双倍消耗格挡值")
    
    def on_damage_before_apply(event: GameEvent):
        """伤害应用前，处理双倍格挡消耗"""
        if event.get_value("double_block_damage", False):
            # 这里可以在Entity.take_damage中读取这个标记
            event.set_value("ignore_block_mechanism", "double")
            print(f"[事件] 准备应用双倍格挡消耗伤害")
    
    def on_card_play_after(event: GameEvent):
        """卡牌打出后，停用破盾效果（一次性效果）"""
        if break_shield_modifier.is_active():
            break_shield_modifier.deactivate()
            print(f"[事件] 破盾效果已消耗")
    
    # 注册事件处理器
    register_event_handler(GameEventType.DAMAGE_CALCULATE, on_damage_calculate, priority=100)
    register_event_handler(GameEventType.DAMAGE_BEFORE_APPLY, on_damage_before_apply, priority=100)
    register_event_handler(GameEventType.CARD_PLAY_AFTER, on_card_play_after, priority=50)


# ==================== 数值修正系统 ====================

class ValueModifier:
    """数值修正器 - 用于修改各种数值"""
    
    def __init__(self, base_value: float):
        self.base_value = base_value
        self.multipliers: List[float] = []  # 乘数列表
        self.additions: List[float] = []    # 加法列表
    
    def add_multiplier(self, multiplier: float):
        """添加乘数修正"""
        self.multipliers.append(multiplier)
    
    def add_addition(self, addition: float):
        """添加加法修正"""
        self.additions.append(addition)
    
    def calculate(self) -> float:
        """计算修正后的值"""
        value = self.base_value
        
        # 先应用所有加法
        for addition in self.additions:
            value += addition
        
        # 再应用所有乘法
        for multiplier in self.multipliers:
            value *= multiplier
        
        return value
    
    def reset(self):
        """重置修正器"""
        self.multipliers.clear()
        self.additions.clear()


def apply_damage_modifiers(base_damage: int, source: Any, target: Any, battle_log=None) -> int:
    """
    应用伤害修正
    
    Args:
        base_damage: 基础伤害
        source: 伤害来源
        target: 伤害目标
        battle_log: 战斗日志（可选）
        
    Returns:
        修正后的伤害值
    """
    modifier = ValueModifier(base_damage)
    
    # 触发伤害计算事件，允许其他系统修改伤害
    event = GameEvent(
        event_type=GameEventType.DAMAGE_CALCULATE,
        source=source,
        target=target,
        data={"damage": base_damage, "battle_log": battle_log}
    )
    global_event_bus.trigger(event)
    
    # 从事件中读取修改后的伤害
    modified_damage = event.get_value("damage", base_damage)
    
    return int(modified_damage)


def apply_heal_modifiers(base_heal: int, source: Any, target: Any, battle_log=None) -> int:
    """
    应用治疗修正
    
    Args:
        base_heal: 基础治疗量
        source: 治疗来源
        target: 治疗目标
        battle_log: 战斗日志（可选）
        
    Returns:
        修正后的治疗量
    """
    modifier = ValueModifier(base_heal)
    
    # 触发治疗计算事件
    event = GameEvent(
        event_type=GameEventType.HEAL_CALCULATE,
        source=source,
        target=target,
        data={"heal": base_heal, "battle_log": battle_log}
    )
    global_event_bus.trigger(event)
    
    # 从事件中读取修改后的治疗量
    modified_heal = event.get_value("heal", base_heal)
    
    return int(modified_heal)


if __name__ == "__main__":
    # 测试事件系统
    print("=== 事件系统测试 ===\n")
    
    # 设置破盾系统
    setup_break_shield_system()
    
    # 测试伤害事件
    print("1. 测试伤害事件:")
    trigger_event(
        GameEventType.DAMAGE_CALCULATE,
        source="刺击卡牌",
        target="敌人",
        data={"damage": 10}
    )
    
    # 测试破盾激活
    print("\n2. 激活破盾效果:")
    break_shield_modifier.activate()
    trigger_event(
        GameEventType.DAMAGE_CALCULATE,
        source="破绽打击",
        target="敌人",
        data={"damage": 15}
    )
    
    print("\n✓ 事件系统测试完成")

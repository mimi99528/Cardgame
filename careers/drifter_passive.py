"""
流浪者职业被动效果实现
"""
from event_system import GameEventType, register_event_handler, GameEvent
from models import Entity, Card
from config import CardTag


class DrifterPassiveHandler:
    """流浪者被动处理器"""
    
    def __init__(self):
        self.registered = False
    
    def register_events(self):
        """注册事件处理器"""
        if self.registered:
            return
        
        # 注册手牌上限修正事件（在抽牌时触发）
        register_event_handler(
            GameEventType.HAND_SIZE_CALCULATE,
            self.on_hand_size_calculate,
            priority=100
        )
        
        self.registered = True
    
    def on_hand_size_calculate(self, event: GameEvent):
        """
        手牌上限计算事件
        流浪者被动：手牌中[移动/探索]标签卡不计入手牌软上限（最多2张）
        """
        entity = event.target
        if not isinstance(entity, Entity):
            return
        
        # 检查实体是否有流浪者职业
        if not hasattr(entity, 'career') or entity.career is None:
            return
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.DRIFTER:
            return
        
        # 获取当前手牌
        hand = event.get_value("hand", [])
        base_hand_size = event.get_value("base_hand_size", 4)
        
        # 统计移动/探索标签的卡牌数量（最多2张不计入）
        movement_exploration_cards = []
        for card in hand:
            if hasattr(card, 'tags') and card.tags:
                has_movement_or_exploration = any(
                    tag in [CardTag.MOVEMENT, CardTag.EXPLORATION]
                    for tag in card.tags
                )
                if has_movement_or_exploration:
                    movement_exploration_cards.append(card)
        
        # 最多2张不计入手牌上限
        excluded_count = min(len(movement_exploration_cards), 2)
        
        # 设置修正后的手牌上限
        modified_hand_size = base_hand_size + excluded_count
        event.set_value("modified_hand_size", modified_hand_size)
        event.set_value("excluded_cards", excluded_count)
        
        # 记录被动触发到战斗日志
        battle_log = event.get_value("battle_log")
        if battle_log and excluded_count > 0:
            battle_log.add(
                f"[流浪者被动] {entity.name}的{excluded_count}张移动/探索卡牌不计入手牌上限",
                level=1,
                color_key="success"
            )


# 全局实例
drifter_passive_handler = DrifterPassiveHandler()


def setup_drifter_passives():
    """设置流浪者被动效果"""
    drifter_passive_handler.register_events()

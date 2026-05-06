"""
农民职业被动效果实现
"""
from event_system import GameEventType, register_event_handler, GameEvent
from models import Entity, Card
from config import CardTag


class FarmerPassiveHandler:
    """农民被动处理器"""
    
    def __init__(self):
        self.registered = False
    
    def register_events(self):
        """注册事件处理器"""
        if self.registered:
            return
        
        # 注册治疗修正事件 - 深耕沃土：[生存]标签卡牌治疗/格挡+2
        register_event_handler(
            GameEventType.HEAL_CALCULATE,
            self.on_heal_calculate,
            priority=60
        )
        
        # 注册格挡计算事件 - 深耕沃土：[生存]标签卡牌格挡+2
        register_event_handler(
            GameEventType.BLOCK_CALCULATE,
            self.on_block_calculate,
            priority=60
        )
        
        self.registered = True
    
    def on_heal_calculate(self, event: GameEvent):
        """
        治疗计算事件
        农民被动：打出带[生存]标签的卡牌时，目标获得的治疗+2（仅对农民自身生效）
        """
        source = event.source
        if not isinstance(source, Card):
            return
        
        # 检查卡牌所有者是否有农民职业
        if not hasattr(source, 'owner') or source.owner is None:
            return
        
        entity = source.owner
        if not hasattr(entity, 'career') or entity.career is None:
            return
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.FARMER:
            return
        
        # 检查卡牌是否有[生存]标签
        has_survival_tag = False
        if hasattr(source, 'tags') and source.tags:
            has_survival_tag = CardTag.SURVIVAL in source.tags
        
        if has_survival_tag:
            current_heal = event.get_value("heal", 0)
            modified_heal = current_heal + 2
            event.set_value("heal", modified_heal)
            
            # 记录被动触发到战斗日志
            battle_log = event.get_value("battle_log")
            if battle_log:
                battle_log.add(
                    f"[农民被动] {entity.name}的{source.name}因[生存]标签治疗+2",
                    level=1,
                    color_key="success"
                )
    
    def on_block_calculate(self, event: GameEvent):
        """
        格挡计算事件
        农民被动：打出带[生存]标签的卡牌时，目标获得的格挡值+2（仅对农民自身生效）
        """
        source = event.source
        if not isinstance(source, Card):
            return
        
        # 检查卡牌所有者是否有农民职业
        if not hasattr(source, 'owner') or source.owner is None:
            return
        
        entity = source.owner
        if not hasattr(entity, 'career') or entity.career is None:
            return
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.FARMER:
            return
        
        # 检查卡牌是否有[生存]标签
        has_survival_tag = False
        if hasattr(source, 'tags') and source.tags:
            has_survival_tag = CardTag.SURVIVAL in source.tags
        
        if has_survival_tag:
            current_block = event.get_value("block", 0)
            modified_block = current_block + 2
            event.set_value("block", modified_block)
            
            # 记录被动触发到战斗日志
            battle_log = event.get_value("battle_log")
            if battle_log:
                battle_log.add(
                    f"[农民被动] {entity.name}的{source.name}因[生存]标签格挡+2",
                    level=1,
                    color_key="success"
                )


# 全局实例
farmer_passive_handler = FarmerPassiveHandler()


def setup_farmer_passives():
    """设置农民被动效果"""
    farmer_passive_handler.register_events()

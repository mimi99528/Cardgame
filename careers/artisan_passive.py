"""
手艺人职业被动效果实现
"""
from event_system import GameEventType, register_event_handler, GameEvent
from models import Entity, Card


class ArtisanPassiveHandler:
    """手艺人被动处理器"""
    
    def __init__(self):
        self.registered = False
    
    def register_events(self):
        """注册事件处理器"""
        if self.registered:
            return
        
        # 注册伤害修正事件
        register_event_handler(
            GameEventType.DAMAGE_CALCULATE,
            self.on_damage_calculate,
            priority=50
        )
        
        # 注册治疗修正事件
        register_event_handler(
            GameEventType.HEAL_CALCULATE,
            self.on_heal_calculate,
            priority=50
        )
        
        self.registered = True
    
    def on_damage_calculate(self, event: GameEvent):
        """
        伤害计算事件
        手艺人被动：装备赋予的卡牌效果+1（伤害）
        """
        source = event.source
        if not isinstance(source, Card):
            return
        
        # 检查卡牌所有者是否有手艺人职业
        if not hasattr(source, 'owner') or source.owner is None:
            return
        
        entity = source.owner
        if not hasattr(entity, 'career') or entity.career is None:
            return
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.ARTISAN:
            return
        
        # 检查卡牌是否来自装备
        if not hasattr(entity, 'equipment_cards'):
            return
        
        is_equipment_card = source in entity.equipment_cards
        
        if is_equipment_card:
            current_damage = event.get_value("damage", 0)
            modified_damage = current_damage + 1
            event.set_value("damage", modified_damage)
            
            # 记录被动触发到战斗日志
            battle_log = event.get_value("battle_log")
            if battle_log:
                battle_log.add(
                    f"[手艺人被动] {entity.name}的装备卡牌{source.name}伤害+1",
                    level=1,
                    color_key="success"
                )
    
    def on_heal_calculate(self, event: GameEvent):
        """
        治疗计算事件
        手艺人被动：装备赋予的卡牌效果+1（回复）
        """
        source = event.source
        if not isinstance(source, Card):
            return
        
        # 检查卡牌所有者是否有手艺人职业
        if not hasattr(source, 'owner') or source.owner is None:
            return
        
        entity = source.owner
        if not hasattr(entity, 'career') or entity.career is None:
            return
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.ARTISAN:
            return
        
        # 检查卡牌是否来自装备
        if not hasattr(entity, 'equipment_cards'):
            return
        
        is_equipment_card = source in entity.equipment_cards
        
        if is_equipment_card:
            current_heal = event.get_value("heal", 0)
            modified_heal = current_heal + 1
            event.set_value("heal", modified_heal)
            
            # 记录被动触发到战斗日志
            battle_log = event.get_value("battle_log")
            if battle_log:
                battle_log.add(
                    f"[手艺人被动] {entity.name}的装备卡牌{source.name}治疗+1",
                    level=1,
                    color_key="success"
                )


# 全局实例
artisan_passive_handler = ArtisanPassiveHandler()


def setup_artisan_passives():
    """设置手艺人被动效果"""
    artisan_passive_handler.register_events()

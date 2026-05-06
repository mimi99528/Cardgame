"""
行商/说书人职业被动效果实现
"""
from event_system import GameEventType, register_event_handler, GameEvent
from models import Entity, Card


class PedlarPassiveHandler:
    """行商/说书人被动处理器"""
    
    def __init__(self):
        self.registered = False
        self.reroll_used_this_encounter = False  # 每场遭遇限1次重掷
    
    def register_events(self):
        """注册事件处理器"""
        if self.registered:
            return
        
        # 注册社交检定相关事件（暂时预留，等待社交系统实现）
        # register_event_handler(
        #     GameEventType.SOCIAL_CHECK_BEFORE,
        #     self.on_social_check_before,
        #     priority=100
        # )
        
        self.registered = True
    
    def on_social_check_before(self, event: GameEvent):
        """
        社交检定前事件
        行商/说书人被动：魅力相关检定结果距(Margin)+1
        """
        entity = event.source
        if not isinstance(entity, Entity):
            return
        
        # 检查实体是否有行商/说书人职业
        if not hasattr(entity, 'career') or entity.career is None:
            return
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.PEDLAR:
            return
        
        # 增加魅力检定的Margin
        current_margin = event.get_value("margin", 0)
        modified_margin = current_margin + 1
        event.set_value("margin", modified_margin)
    
    def can_reroll_social_check(self, entity: Entity) -> bool:
        """
        检查是否可以重掷社交检定
        行商/说书人被动：非主线剧情类社交检定失败时可消耗1点幸运重掷（每场遭遇限1次）
        """
        if not isinstance(entity, Entity):
            return False
        
        if not hasattr(entity, 'career') or entity.career is None:
            return False
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.PEDLAR:
            return False
        
        # 检查是否已经使用过重掷
        if self.reroll_used_this_encounter:
            return False
        
        # 检查是否有足够的幸运值
        if entity.stats.luck < 1:
            return False
        
        return True
    
    def use_reroll(self, entity: Entity) -> bool:
        """
        使用重掷机会
        返回是否成功使用
        """
        if not self.can_reroll_social_check(entity):
            return False
        
        # 消耗1点幸运
        entity.stats.luck -= 1
        self.reroll_used_this_encounter = True
        
        return True
    
    def reset_encounter(self):
        """重置遭遇计数器（新遭遇开始时调用）"""
        self.reroll_used_this_encounter = False


# 全局实例
pedlar_passive_handler = PedlarPassiveHandler()


def setup_pedlar_passives():
    """设置行商/说书人被动效果"""
    pedlar_passive_handler.register_events()

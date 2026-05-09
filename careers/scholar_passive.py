"""
游学青年职业被动效果实现
"""
from event_system import GameEventType, register_event_handler, GameEvent
from models import Entity, Card
from config import CardTag


class ScholarPassiveHandler:
    """游学青年被动处理器"""
    
    def __init__(self):
        self.registered = False
        self.per_entity_first_card = {}  # 记录每个实体是否已触发过首次抽牌
    
    def register_events(self):
        """注册事件处理器"""
        if self.registered:
            return
        
        # 注册卡牌打出后事件 - 博闻强记①：每场遭遇首次打出[知识]或[法术]卡时，额外抽1张牌
        register_event_handler(
            GameEventType.CARD_PLAY_AFTER,
            self.on_card_play_after,
            priority=70
        )
        
        # 注册社交检定前事件 - 博闻强记②：心智调整值用于社交检定时，+1加值
        register_event_handler(
            GameEventType.SOCIAL_CHECK_BEFORE,
            self.on_social_check_before,
            priority=70
        )
        
        # 注册节点移动事件 - 博闻强记③：大地图移动时，若目的地是[知识]类节点，消耗资源-1
        register_event_handler(
            GameEventType.NODE_TRAVEL,
            self.on_node_travel,
            priority=70
        )
        
        self.registered = True
    
    def on_card_play_after(self, event: GameEvent):
        """
        卡牌打出后事件
        游学青年被动①：每场遭遇首次打出[知识]或[法术]卡时，额外抽1张牌（限1次）
        """
        source = event.source
        if not isinstance(source, Card):
            return
        
        # 检查卡牌所有者是否有游学青年职业
        if not hasattr(source, 'owner') or source.owner is None:
            return
        
        entity = source.owner
        if not hasattr(entity, 'career') or entity.career is None:
            return
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.SCHOLAR:
            return
        
        # 检查卡牌是否有[知识]或[法术]标签
        has_knowledge_or_spell = False
        if hasattr(source, 'tags') and source.tags:
            # 支持枚举类型和字符串类型的标签
            has_knowledge_or_spell = ((CardTag.KNOWLEDGE in source.tags or "知识" in source.tags) or 
                                     (CardTag.SPELL in source.tags or "法术" in source.tags))
        
        if not has_knowledge_or_spell:
            return
        
        # 检查该实体是否已经触发过（每场遭遇限1次）
        entity_id = id(entity)
        if entity_id in self.per_entity_first_card:
            return
        
        # 标记已触发
        self.per_entity_first_card[entity_id] = True
        
        # 额外抽1张牌
        if hasattr(entity, 'deck') and len(entity.deck) > 0:
            import random
            drawn_card = random.choice(entity.deck)
            entity.deck.remove(drawn_card)
            drawn_card.owner = entity  # 设置卡牌所有者
            entity.hand.append(drawn_card)
            
            # 记录被动触发到战斗日志
            battle_log = event.get_value("battle_log")
            if battle_log:
                battle_log.add(
                    f"[游学青年被动] {entity.name}打出{source.name}，额外抽取1张牌",
                    level=1,
                    color_key="success"
                )
    
    def on_social_check_before(self, event: GameEvent):
        """
        社交检定前事件
        游学青年被动②：心智调整值用于社交检定时，+1加值（学识说服）
        """
        entity = event.target
        if not isinstance(entity, Entity):
            return
        
        # 检查实体是否有游学青年职业
        if not hasattr(entity, 'career') or entity.career is None:
            return
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.SCHOLAR:
            return
        
        # 获取当前社交检定加值并+1
        current_bonus = event.get_value("bonus", 0)
        modified_bonus = current_bonus + 1
        event.set_value("bonus", modified_bonus)
        
        # 记录被动触发到战斗日志
        battle_log = event.get_value("battle_log")
        if battle_log:
            battle_log.add(
                f"[游学青年被动] {entity.name}的社交检定因学识说服+1",
                level=1,
                color_key="success"
            )
    
    def on_node_travel(self, event: GameEvent):
        """
        节点移动事件
        游学青年被动③：大地图移动时，若目的地是[知识]类节点，消耗资源-1
        """
        entity = event.target
        if not isinstance(entity, Entity):
            return
        
        # 检查实体是否有游学青年职业
        if not hasattr(entity, 'career') or entity.career is None:
            return
        
        from career_system import CareerType
        if entity.career.career_type != CareerType.SCHOLAR:
            return
        
        # 检查目的地是否是[知识]类节点
        destination_node = event.get_value("destination")
        if not destination_node:
            return
        
        # 假设节点有tags属性，检查是否有KNOWLEDGE标签
        is_knowledge_node = False
        if hasattr(destination_node, 'tags') and destination_node.tags:
            is_knowledge_node = CardTag.KNOWLEDGE in destination_node.tags
        
        if is_knowledge_node:
            # 减少资源消耗
            current_cost = event.get_value("resource_cost", 0)
            modified_cost = max(0, current_cost - 1)
            event.set_value("resource_cost", modified_cost)
            
            # 记录被动触发到战斗日志
            battle_log = event.get_value("battle_log")
            if battle_log:
                battle_log.add(
                    f"[游学青年被动] {entity.name}前往知识节点，资源消耗-1",
                    level=1,
                    color_key="success"
                )
    
    def reset_encounter_state(self):
        """重置遭遇状态（新遭遇开始时调用）"""
        self.per_entity_first_card.clear()


# 全局实例
scholar_passive_handler = ScholarPassiveHandler()


def setup_scholar_passives():
    """设置游学青年被动效果"""
    scholar_passive_handler.register_events()

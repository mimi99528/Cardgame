"""
卡牌序列化模块
提供卡牌对象与JSON格式之间的转换功能
"""
import json
from typing import Dict, List, Any, Optional
from models import Card, Weapon, Armor
from config import CardType, Rarity, TargetType


class CardSerializer:
    """卡牌序列化器 - 负责卡牌的序列化和反序列化"""
    
    @staticmethod
    def is_equipment_card(data: Dict[str, Any]) -> bool:
        """
        判断是否为装备卡牌
        
        Args:
            data: 卡牌数据字典
            
        Returns:
            是否为装备卡牌
        """
        return (data.get("type") == "equipment" and 
                data.get("category") in ["item", "item-accessory"])
    
    @staticmethod
    def card_to_dict(card: Card, card_id: int = None) -> Dict[str, Any]:
        """
        将卡牌对象转换为字典（使用结构化列表格式）
        
        Args:
            card: 卡牌对象
            card_id: 卡牌ID（可选，如果不提供则使用Python对象ID）
            
        Returns:
            包含卡牌信息的字典
        """
        card_dict = {
            "id": card_id if card_id is not None else id(card),
            "name": card.name,
            "category": "combat",  # 卡牌分类
            "type": card.card_type.value,  # 存储枚举的值字符串
            "description": card.description,
            "rarity": card.rarity.name,  # 存储枚举的名称
            "ap_cost": card.ap_cost,
            "effects": card.effects if isinstance(card.effects, list) else [],  # 结构化效果列表
            "play_conditions": [],  # 预留字段：打出条件列表
            "atk_dis": card.atk_dis,  # 攻击距离
            "atk_rnge": card.atk_rnge,  # 攻击范围
            "target_type": card.target_type.value,  # 目标类型
            "is_movement": card.is_movement,  # 是否为移动卡牌
            "mp_cost": card.mp_cost,  # MP消耗
            "stat_ratios": card.stat_ratios if card.stat_ratios else {}  # 属性比例
        }
        
        # 添加升级信息（如果有）
        if card.upgrade:
            card_dict["upgrade"] = {
                "level": card.upgrade.level,
                "upgrades": card.upgrade.upgrades
            }
        
        # 添加进化信息（如果有）
        if card.evolved_from:
            card_dict["evolved_from"] = card.evolved_from
        if card.can_evolve_to:
            card_dict["can_evolve_to"] = card.can_evolve_to
        
        return card_dict
    
    @staticmethod
    def dict_to_card(data: Dict[str, Any]) -> Card:
        """
        从字典创建卡牌对象
        
        Args:
            data: 包含卡牌信息的字典
            
        Returns:
            卡牌对象
            
        Raises:
            ValueError: 当数据无效时
            KeyError: 当缺少必要字段时
        """
        # 检查是否为装备卡牌
        if CardSerializer.is_equipment_card(data):
            return CardSerializer._dict_to_equipment(data)
        
        # 验证必要字段
        required_fields = ["name", "type", "description", "ap_cost"]
        for field in required_fields:
            if field not in data:
                raise KeyError(f"缺少必要字段: {field}")
        
        # 转换卡牌类型
        try:
            card_type = CardType(data["type"])
        except ValueError:
            raise ValueError(f"无效的卡牌类型: {data['type']}")
        
        # 转换稀有度（如果有）
        rarity = Rarity.COMMON  # 默认稀有度
        if "rarity" in data:
            try:
                rarity = Rarity[data["rarity"]]
            except KeyError:
                raise ValueError(f"无效的稀有度: {data['rarity']}")
        
        # 获取effects（必须是列表格式）
        effects = data.get("effects", [])
        if not isinstance(effects, list):
            raise ValueError(f"卡牌 '{data.get('name', 'Unknown')}' 的effects必须是列表格式")
        
        # 创建卡牌对象
        card = Card(
            name=data["name"],
            card_type=card_type,
            ap_cost=data["ap_cost"],
            effects=effects,  # 直接使用结构化列表
            description=data["description"],
            rarity=rarity,
            atk_dis=data.get("atk_dis", 1),  # 默认攻击距离为1（近战）
            atk_rnge=data.get("atk_rnge", {"type": "circle", "radius": 1}),  # 默认攻击范围为半径1的圆形
            target_type=TargetType(data.get("target_type", "enemy")),  # 默认目标类型为敌人
            is_movement=data.get("is_movement", False),
            mp_cost=data.get("mp_cost", 0),  # 默认MP消耗为0
            stat_ratios=data.get("stat_ratios", {})  # 默认无属性比例
        )
        
        # 恢复升级信息（如果有）
        if "upgrade" in data:
            from models import CardUpgrade
            upgrade_data = data["upgrade"]
            card.upgrade = CardUpgrade(
                level=upgrade_data.get("level", 0),
                upgrades=upgrade_data.get("upgrades", [])
            )
        
        # 恢复进化信息（如果有）
        if "evolved_from" in data:
            card.evolved_from = data["evolved_from"]
        if "can_evolve_to" in data:
            card.can_evolve_to = data["can_evolve_to"]
        
        return card
    
    @staticmethod
    def _dict_to_equipment(data: Dict[str, Any]):
        """
        从字典创建装备对象（武器或防具）
        
        Args:
            data: 包含装备信息的字典
            
        Returns:
            Weapon 或 Armor 对象
        """
        # 验证必要字段
        required_fields = ["name", "description", "equipment_type"]
        for field in required_fields:
            if field not in data:
                raise KeyError(f"缺少必要字段: {field}")
        
        # 转换稀有度
        rarity = Rarity.COMMON
        if "rarity" in data:
            try:
                rarity = Rarity[data["rarity"]]
            except KeyError:
                raise ValueError(f"无效的稀有度: {data['rarity']}")
        
        equipment_type = data["equipment_type"]
        equipment_stats = data.get("equipment_stats", {})
        
        if equipment_type == "weapon":
            # 创建武器
            weapon = Weapon(
                name=data["name"],
                description=data["description"],
                rarity=rarity,
                physical_bonus=equipment_stats.get("physical_bonus", 0),
                magical_bonus=equipment_stats.get("magical_bonus", 0),
                attack_modifier=equipment_stats.get("attack_modifier", 0),
                provided_cards=equipment_stats.get("provided_cards", [])
            )
            return weapon
        
        elif equipment_type == "armor":
            # 创建防具
            armor = Armor(
                name=data["name"],
                description=data["description"],
                rarity=rarity,
                block_value=equipment_stats.get("block_value", 0),
                block_dice=equipment_stats.get("block_dice", ""),
                block_per_turn=equipment_stats.get("block_per_turn", 0),
                ap_bonus=equipment_stats.get("ap_bonus", 0),
                provided_cards=equipment_stats.get("provided_cards", [])
            )
            return armor
        
        elif equipment_type == "accessory":
            # 创建饰品
            from models import Accessory
            accessory = Accessory(
                name=data["name"],
                description=data["description"],
                rarity=rarity,
                stat_bonuses=equipment_stats.get("stat_bonuses", {}),
                special_effects=data.get("effects", [])
            )
            return accessory
        
        else:
            raise ValueError(f"未知的装备类型: {equipment_type}")
    
    @staticmethod
    def cards_to_json(cards: List[Card], indent: int = 2, start_id: int = 1) -> str:
        """
        将卡牌列表转换为JSON字符串
        
        Args:
            cards: 卡牌列表
            indent: JSON缩进空格数
            start_id: 起始ID（默认从1开始）
            
        Returns:
            JSON字符串
        """
        cards_data = []
        for i, card in enumerate(cards):
            card_dict = CardSerializer.card_to_dict(card, card_id=start_id + i)
            cards_data.append(card_dict)
        return json.dumps(cards_data, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def json_to_cards(json_str: str) -> List[Card]:
        """
        从JSON字符串创建卡牌列表
        
        Args:
            json_str: JSON字符串
            
        Returns:
            卡牌列表
        """
        cards_data = json.loads(json_str)
        return [CardSerializer.dict_to_card(data) for data in cards_data]
    
    @staticmethod
    def save_cards_to_file(cards: List[Card], filepath: str):
        """
        将卡牌列表保存到JSON文件
        
        Args:
            cards: 卡牌列表
            filepath: 文件路径
        """
        json_str = CardSerializer.cards_to_json(cards)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    @staticmethod
    def load_cards_from_file(filepath: str) -> List[Card]:
        """
        从JSON文件加载卡牌列表
        
        Args:
            filepath: 文件路径
            
        Returns:
            卡牌列表
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            json_str = f.read()
        return CardSerializer.json_to_cards(json_str)
    
    @staticmethod
    def equipment_to_dict(equipment, equipment_id: int = None) -> Dict[str, Any]:
        """
        将装备对象转换为字典
        
        Args:
            equipment: Weapon 或 Armor 对象
            equipment_id: 装备ID
            
        Returns:
            包含装备信息的字典
        """
        from models import Weapon, Armor
        
        base_dict = {
            "id": equipment_id if equipment_id is not None else id(equipment),
            "name": equipment.name,
            "category": "item",
            "type": "equipment",
            "description": equipment.description,
            "rarity": equipment.rarity.name,
            "ap_cost": 0,  # 装备不消耗AP
            "effects": [],
            "play_conditions": []
        }
        
        if isinstance(equipment, Weapon):
            base_dict["equipment_type"] = "weapon"
            base_dict["equipment_stats"] = {
                "physical_bonus": equipment.physical_bonus,
                "magical_bonus": equipment.magical_bonus,
                "attack_modifier": equipment.attack_modifier,
                "provided_cards": equipment.provided_cards
            }
        elif isinstance(equipment, Armor):
            base_dict["equipment_type"] = "armor"
            base_dict["equipment_stats"] = {
                "block_value": equipment.block_value,
                "block_dice": equipment.block_dice,
                "block_per_turn": equipment.block_per_turn,
                "ap_bonus": equipment.ap_bonus,
                "provided_cards": equipment.provided_cards
            }
        
        return base_dict
    
    @staticmethod
    def load_equipments_from_file(filepath: str):
        """
        从JSON文件加载装备列表
        
        Args:
            filepath: 文件路径
            
        Returns:
            装备列表（Weapon和Armor对象）
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
        
        equipments = []
        for data in data_list:
            if CardSerializer.is_equipment_card(data):
                equipment = CardSerializer._dict_to_equipment(data)
                equipments.append(equipment)
        
        return equipments


# ==================== 扩展功能：支持复杂条件和效果 ====================

class ConditionEffectSerializer:
    """条件和效果序列化器 - 处理复杂的打出条件和效果"""
    
    # 效果类型定义
    EFFECT_TYPES = {
        "emy_dmg": "敌方伤害",
        "self_heal": "自我治疗",
        "self_block": "自我格挡",
        "emy_debuff": "敌方减益",
        "self_buff": "自我增益",
    }
    
    # 条件类型定义
    CONDITION_TYPES = {
        "min_ap": "最低AP要求",
        "enemy_hp_below": "敌人生命值低于阈值",
        "has_buff": "目标拥有特定Buff",
        "turn_number": "回合数要求",
        "card_in_hand": "手牌中有特定卡牌",
    }
    
    @staticmethod
    def create_effect(effect_type: str, **kwargs) -> Dict[str, Any]:
        """
        创建结构化效果
        
        Args:
            effect_type: 效果类型，如 "emy_dmg", "self_heal" 等
            **kwargs: 效果参数
            
        Returns:
            结构化效果字典
            
        Examples:
            >>> create_effect("emy_dmg", amount=10)
            {'type': 'emy_dmg', 'amount': 10}
            
            >>> create_effect("emy_debuff", buff_type="pot", stacks=3, duration=3)
            {'type': 'emy_debuff', 'buff_type': 'pot', 'stacks': 3, 'duration': 3}
        """
        effect = {"type": effect_type}
        effect.update(kwargs)
        return effect
    
    @staticmethod
    def create_condition(condition_type: str, **kwargs) -> Dict[str, Any]:
        """
        创建结构化打出条件
        
        Args:
            condition_type: 条件类型，如 "min_ap", "enemy_hp_below" 等
            **kwargs: 条件参数
            
        Returns:
            结构化条件字典
            
        Examples:
            >>> create_condition("min_ap", value=2)
            {'type': 'min_ap', 'value': 2}
            
            >>> create_condition("enemy_hp_below", percentage=50)
            {'type': 'enemy_hp_below', 'percentage': 50}
        """
        condition = {"type": condition_type}
        condition.update(kwargs)
        return condition
    
    @staticmethod
    def condition_to_dict(condition: Dict[str, Any]) -> Dict[str, Any]:
        """
        将打出条件转换为字典
        
        条件示例格式：
        {
            "type": "min_ap",
            "value": 2,
            "description": "需要至少2点AP"
        }
        
        Args:
            condition: 条件字典
            
        Returns:
            序列化后的条件字典
        """
        return condition.copy()
    
    @staticmethod
    def effect_to_dict(effect: Dict[str, Any]) -> Dict[str, Any]:
        """
        将效果转换为字典
        
        效果示例格式：
        {
            "type": "damage",
            "value": 25,
            "target": "enemy",
            "description": "造成25点伤害"
        }
        
        Args:
            effect: 效果字典
            
        Returns:
            序列化后的效果字典
        """
        return effect.copy()
    
    @staticmethod
    def conditions_list_to_dict(conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """序列化条件列表"""
        return [ConditionEffectSerializer.condition_to_dict(c) for c in conditions]
    
    @staticmethod
    def effects_list_to_dict(effects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """序列化效果列表"""
        return [ConditionEffectSerializer.effect_to_dict(e) for e in effects]


# ==================== 便捷函数 ====================

def serialize_card(card: Card, card_id: int = None) -> Dict[str, Any]:
    """便捷函数：序列化单个卡牌"""
    return CardSerializer.card_to_dict(card, card_id=card_id)


def deserialize_card(data: Dict[str, Any]) -> Card:
    """便捷函数：反序列化单个卡牌"""
    return CardSerializer.dict_to_card(data)


def serialize_cards_to_json(cards: List[Card], start_id: int = 1) -> str:
    """便捷函数：序列化卡牌列表为JSON"""
    return CardSerializer.cards_to_json(cards, start_id=start_id)


def deserialize_cards_from_json(json_str: str) -> List[Card]:
    """便捷函数：从JSON反序列化卡牌列表"""
    return CardSerializer.json_to_cards(json_str)

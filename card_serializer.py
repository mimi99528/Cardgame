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
        return (data.get("category") == "item" and 
                data.get("type") == "equipment")
    
    @staticmethod
    def _convert_effects_to_list(effects_dict: Dict[str, any]) -> List[Dict[str, Any]]:
        """
        将effects字典转换为结构化列表格式
        
        Args:
            effects_dict: 原始effects字典，如 {"hp": -10, "block": 25}
            
        Returns:
            结构化效果列表
        """
        # 如果已经是列表格式，直接返回
        if isinstance(effects_dict, list):
            return effects_dict
        
        effects_list = []
        
        for key, value in effects_dict.items():
            effect = CardSerializer._parse_effect_key_value(key, value)
            if effect:
                effects_list.append(effect)
        
        return effects_list
    
    @staticmethod
    def _parse_effect_key_value(key: str, value: any) -> Dict[str, Any]:
        """
        解析effect键值对为结构化格式
        
        Args:
            key: 效果键名，如 "hp", "block", "pot_3"
            value: 效果值
            
        Returns:
            结构化效果字典
        """
        # 伤害/治疗效果
        if key == "hp":
            if value < 0:
                return {
                    "type": "emy_dmg",
                    "amount": abs(value)
                }
            else:
                return {
                    "type": "self_heal",
                    "amount": value
                }
        
        # 格挡效果
        elif key == "block":
            return {
                "type": "self_block",
                "amount": value
            }
        
        # Buff/Debuff效果（如 pot_3）
        elif "_" in key:
            parts = key.split("_")
            buff_prefix = parts[0]
            
            # 查找对应的BuffType
            from config import BuffType
            for buff_type in BuffType:
                if buff_type.value == buff_prefix:
                    # value就是实际的层数
                    actual_stacks = value
                    
                    # 判断是Debuff还是Buff
                    if buff_prefix in ["pot"]:  # Debuff
                        return {
                            "type": "emy_debuff",
                            "buff_type": buff_type.value,
                            "stacks": actual_stacks,
                            "duration": -1  # -1表示永久
                        }
                    else:  # Buff
                        return {
                            "type": "self_buff",
                            "buff_type": buff_type.value,
                            "stacks": actual_stacks,
                            "duration": -1
                        }
        
        # 未知效果类型，保留原始格式
        return {
            "type": key,
            "value": value
        }
    
    @staticmethod
    def _convert_effects_list_to_dict(effects_list: List[Dict[str, Any]]) -> Dict[str, any]:
        """
        将结构化效果列表转换回字典格式（用于创建Card对象）
        
        Args:
            effects_list: 结构化效果列表
            
        Returns:
            effects字典
        """
        effects_dict = {}
        
        for effect in effects_list:
            effect_type = effect.get("type", "")
            
            # 敌方伤害
            if effect_type == "emy_dmg":
                # 优先使用dice表达式，否则使用amount
                if "dice" in effect:
                    # 对于dice表达式，我们暂时存储为特殊标记
                    effects_dict["hp_dice"] = effect["dice"]
                elif "amount" in effect:
                    effects_dict["hp"] = -effect.get("amount", 0)
            
            # 自我治疗
            elif effect_type == "self_heal":
                effects_dict["hp"] = effect.get("amount", 0)
            
            # 自我格挡
            elif effect_type == "self_block":
                # 优先使用dice表达式，否则使用amount
                if "dice" in effect:
                    effects_dict["block_dice"] = effect["dice"]
                elif "amount" in effect:
                    effects_dict["block"] = effect.get("amount", 0)
            
            # 敌方Debuff
            elif effect_type == "emy_debuff":
                buff_type = effect.get("buff_type", "")
                stacks = effect.get("stacks", 1)
                # 使用stacks值作为键名的一部分，保持与原始格式一致
                key = f"{buff_type}_{stacks}"
                effects_dict[key] = stacks
            
            # 自我Buff
            elif effect_type == "self_buff":
                buff_type = effect.get("buff_type", "")
                stacks = effect.get("stacks", 1)
                # 使用stacks值作为键名的一部分，保持与原始格式一致
                key = f"{buff_type}_{stacks}"
                effects_dict[key] = stacks
            
            # 其他类型，尝试直接使用
            else:
                if "value" in effect:
                    effects_dict[effect_type] = effect["value"]
                elif "amount" in effect:
                    effects_dict[effect_type] = effect["amount"]
        
        return effects_dict
    
    @staticmethod
    def card_to_dict(card: Card, card_id: int = None) -> Dict[str, Any]:
        """
        将卡牌对象转换为字典
        
        Args:
            card: 卡牌对象
            card_id: 卡牌ID（可选，如果不提供则使用Python对象ID）
            
        Returns:
            包含卡牌信息的字典
        """
        # 转换effects为结构化列表格式
        effects_list = CardSerializer._convert_effects_to_list(card.effects)
        
        return {
            "id": card_id if card_id is not None else id(card),
            "name": card.name,
            "category": "combat",  # 卡牌分类
            "type": card.card_type.value,  # 存储枚举的值字符串
            "description": card.description,
            "rarity": card.rarity.name,  # 存储枚举的名称
            "ap_cost": card.ap_cost,
            "effects": effects_list,  # 结构化效果列表
            "play_conditions": [],  # 预留字段：打出条件列表
            "atk_dis": card.atk_dis,  # 攻击距离
            "atk_rnge": card.atk_rnge,  # 攻击范围
            "target_type": card.target_type.value  # 目标类型
        }
    
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
        
        # 转换effects：支持列表格式和旧版字典格式
        effects_dict = {}
        if "effects" in data:
            if isinstance(data["effects"], list):
                # 新格式：结构化列表
                effects_dict = CardSerializer._convert_effects_list_to_dict(data["effects"])
            elif isinstance(data["effects"], dict):
                # 旧格式：字典（向后兼容）
                effects_dict = data["effects"]
        
        # 创建卡牌对象
        card = Card(
            name=data["name"],
            card_type=card_type,
            ap_cost=data["ap_cost"],
            effects=effects_dict,
            description=data["description"],
            rarity=rarity,
            atk_dis=data.get("atk_dis", 1),  # 默认攻击距离为1（近战）
            atk_rnge=data.get("atk_rnge", {"type": "circle", "radius": 1}),  # 默认攻击范围为半径1的圆形
            target_type=TargetType(data.get("target_type", "enemy")),  # 默认目标类型为敌人
            is_movement=data.get("is_movement", False)
        )
        
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

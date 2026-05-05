"""
卡牌升级与进化系统模块
提供卡牌升级、进化和牌库管理功能
"""
from typing import Dict, List, Optional, Tuple
from copy import deepcopy
import random
from models import Card, CardUpgrade
from config import Rarity


class CardEvolutionChain:
    """卡牌进化链 - 定义卡牌的进化路径"""
    
    def __init__(self, base_card_name: str):
        self.base_card_name = base_card_name  # 基础卡牌名称
        self.evolution_path: List[str] = []   # 进化路径 [基础卡, 一阶进化, 二阶进化, ...]
        self.evolution_requirements: Dict[str, Dict] = {}  # 每个进化阶段的要求
    
    def add_evolution_stage(self, next_card_name: str, requirements: Dict = None):
        """添加进化阶段"""
        if not self.evolution_path:
            self.evolution_path.append(self.base_card_name)
        
        self.evolution_path.append(next_card_name)
        if requirements:
            self.evolution_requirements[next_card_name] = requirements
    
    def get_next_evolution(self, current_card_name: str) -> Optional[str]:
        """获取下一个进化形态"""
        if current_card_name in self.evolution_path:
            current_index = self.evolution_path.index(current_card_name)
            if current_index < len(self.evolution_path) - 1:
                return self.evolution_path[current_index + 1]
        return None
    
    def can_evolve(self, current_card_name: str) -> bool:
        """检查是否可以进化"""
        return self.get_next_evolution(current_card_name) is not None


class CardUpgradeSystem:
    """卡牌升级系统"""
    
    def __init__(self):
        self.upgrade_templates: Dict[str, List[Dict]] = {}  # 升级模板
    
    def register_upgrade_template(self, card_name: str, upgrades: List[Dict]):
        """注册卡牌升级模板"""
        self.upgrade_templates[card_name] = upgrades
    
    def upgrade_card(self, card: Card, upgrade_level: int = 1) -> Card:
        """
        升级卡牌
        
        Args:
            card: 要升级的卡牌
            upgrade_level: 升级等级
            
        Returns:
            升级后的新卡牌
        """
        # 创建卡牌副本
        upgraded_card = card.copy()
        
        # 初始化升级信息
        if upgraded_card.upgrade is None:
            upgraded_card.upgrade = CardUpgrade()
        
        # 应用升级效果
        template_upgrades = self.upgrade_templates.get(card.name, [])
        
        for i in range(upgrade_level):
            if i < len(template_upgrades):
                upgrade_info = template_upgrades[i]
                upgrade_type = upgrade_info.get("type", "")
                value = upgrade_info.get("value", 0)
                description = upgrade_info.get("description", "")
                
                # 应用不同类型的升级
                if upgrade_type == "damage_increase":
                    # 增加伤害
                    self._apply_damage_upgrade(upgraded_card, value)
                elif upgrade_type == "ap_cost_reduction":
                    # 减少AP消耗
                    upgraded_card.ap_cost = max(0, upgraded_card.ap_cost - value)
                elif upgrade_type == "add_effect":
                    # 添加新效果
                    self._add_effect_to_card(upgraded_card, value)
                elif upgrade_type == "range_increase":
                    # 增加攻击范围
                    self._increase_attack_range(upgraded_card, value)
                
                # 记录升级
                upgraded_card.upgrade.add_upgrade(upgrade_type, value, description)
        
        # 更新描述以反映升级
        upgraded_card.description += f" (升级Lv.{upgraded_card.upgrade.level})"
        
        return upgraded_card
    
    def _apply_damage_upgrade(self, card: Card, damage_increase: int):
        """应用伤害升级"""
        if isinstance(card.effects, dict):
            if "hp" in card.effects:
                card.effects["hp"] -= damage_increase  # 负值表示伤害，所以减去正值
        elif isinstance(card.effects, list):
            for effect in card.effects:
                if effect.get("type") == "emy_dmg":
                    if "amount" in effect:
                        effect["amount"] += damage_increase
    
    def _add_effect_to_card(self, card: Card, new_effect: Dict):
        """向卡牌添加新效果"""
        if isinstance(card.effects, list):
            card.effects.append(new_effect)
        elif isinstance(card.effects, dict):
            # 将字典格式转换为列表格式并添加新效果
            effects_list = []
            for key, value in card.effects.items():
                effects_list.append({"type": key, "value": value})
            effects_list.append(new_effect)
            card.effects = effects_list
    
    def _increase_attack_range(self, card: Card, range_increase: int):
        """增加攻击范围"""
        if hasattr(card, 'atk_rnge') and card.atk_rnge:
            if "radius" in card.atk_rnge:
                card.atk_rnge["radius"] += range_increase


class CardEvolutionSystem:
    """卡牌进化系统"""
    
    def __init__(self):
        self.evolution_chains: Dict[str, CardEvolutionChain] = {}  # 进化链
        self.card_database: Dict[str, Card] = {}  # 卡牌数据库引用
    
    def register_evolution_chain(self, chain: CardEvolutionChain):
        """注册进化链"""
        self.evolution_chains[chain.base_card_name] = chain
    
    def set_card_database(self, database: Dict[str, Card]):
        """设置卡牌数据库引用"""
        self.card_database = database
    
    def evolve_card(self, card: Card) -> Optional[Card]:
        """
        进化卡牌
        
        Args:
            card: 要进化的卡牌
            
        Returns:
            进化后的新卡牌，如果无法进化则返回None
        """
        # 查找对应的进化链
        evolution_chain = None
        for chain in self.evolution_chains.values():
            if card.name in chain.evolution_path:
                evolution_chain = chain
                break
        
        if not evolution_chain:
            return None
        
        # 获取下一个进化形态
        next_evolution_name = evolution_chain.get_next_evolution(card.name)
        if not next_evolution_name:
            return None
        
        # 从数据库中获取进化后的卡牌
        if next_evolution_name not in self.card_database:
            return None
        
        evolved_card = self.card_database[next_evolution_name].copy()
        
        # 设置进化相关信息
        evolved_card.evolved_from = card.name
        evolved_card.can_evolve_to = evolution_chain.get_next_evolution(next_evolution_name)
        
        # 如果有升级信息，部分继承
        if card.upgrade:
            # 可以设计一些升级效果的继承逻辑
            pass
        
        return evolved_card
    
    def can_evolve(self, card: Card) -> bool:
        """检查卡牌是否可以进化"""
        for chain in self.evolution_chains.values():
            if card.name in chain.evolution_path:
                return chain.can_evolve(card.name)
        return False


class CardLibrary:
    """牌库系统 - 管理玩家拥有的所有卡牌"""
    
    def __init__(self, max_capacity: int = 100):
        self.library: Dict[str, List[Card]] = {}  # 按名称分组的卡牌收藏
        self.max_capacity = max_capacity  # 牌库最大容量
        self.total_cards = 0  # 当前卡牌总数
    
    def add_card(self, card: Card) -> bool:
        """
        添加卡牌到牌库
        
        Args:
            card: 要添加的卡牌
            
        Returns:
            是否成功添加
        """
        if self.total_cards >= self.max_capacity:
            return False  # 牌库已满
        
        if card.name not in self.library:
            self.library[card.name] = []
        
        self.library[card.name].append(card)
        self.total_cards += 1
        return True
    
    def remove_card(self, card_name: str, index: int = 0) -> Optional[Card]:
        """
        从牌库移除卡牌
        
        Args:
            card_name: 卡牌名称
            index: 卡牌索引（同名卡牌可能有多个）
            
        Returns:
            被移除的卡牌，如果不存在则返回None
        """
        if card_name in self.library and len(self.library[card_name]) > index:
            removed_card = self.library[card_name].pop(index)
            self.total_cards -= 1
            
            # 如果该名称下没有卡牌了，删除键
            if not self.library[card_name]:
                del self.library[card_name]
            
            return removed_card
        return None
    
    def get_card(self, card_name: str, index: int = 0) -> Optional[Card]:
        """获取牌库中的卡牌"""
        if card_name in self.library and len(self.library[card_name]) > index:
            return self.library[card_name][index]
        return None
    
    def get_cards_by_name(self, card_name: str) -> List[Card]:
        """获取指定名称的所有卡牌"""
        return self.library.get(card_name, []).copy()
    
    def get_all_cards(self) -> List[Card]:
        """获取牌库中所有卡牌"""
        all_cards = []
        for cards in self.library.values():
            all_cards.extend(cards)
        return all_cards
    
    def has_card(self, card_name: str) -> bool:
        """检查是否拥有指定卡牌"""
        return card_name in self.library and len(self.library[card_name]) > 0
    
    def get_card_count(self, card_name: str) -> int:
        """获取指定卡牌的数量"""
        return len(self.library.get(card_name, []))
    
    def get_library_info(self) -> Dict:
        """获取牌库信息"""
        return {
            "total_cards": self.total_cards,
            "max_capacity": self.max_capacity,
            "unique_cards": len(self.library),
            "capacity_usage": self.total_cards / self.max_capacity if self.max_capacity > 0 else 0
        }
    
    def create_deck_from_library(self, deck_config: Dict[str, int], max_deck_size: int = 30) -> List[Card]:
        """
        从牌库创建卡组
        
        Args:
            deck_config: 卡组配置，{卡牌名称: 数量}
            max_deck_size: 卡组最大大小
            
        Returns:
            构建的卡组
        """
        deck = []
        
        for card_name, count in deck_config.items():
            if self.has_card(card_name):
                available_cards = self.get_cards_by_name(card_name)
                # 取所需数量和可用数量的较小值
                actual_count = min(count, len(available_cards))
                
                for i in range(actual_count):
                    if len(deck) < max_deck_size:
                        # 复制卡牌用于卡组
                        deck.append(available_cards[i].copy())
                    else:
                        break
                        
                if len(deck) >= max_deck_size:
                    break
        
        return deck


def create_example_evolution_system(card_db: Dict[str, Card]) -> Tuple[CardEvolutionSystem, CardUpgradeSystem]:
    """创建示例进化和升级系统"""
    
    # 创建进化系统
    evolution_system = CardEvolutionSystem()
    evolution_system.set_card_database(card_db)
    
    # 创建示例进化链：刺击 -> 精准刺击 -> 致命刺击
    thrust_chain = CardEvolutionChain("刺击")
    thrust_chain.add_evolution_stage("精准刺击", {"requirement": "level_5"})
    thrust_chain.add_evolution_stage("致命刺击", {"requirement": "level_10"})
    evolution_system.register_evolution_chain(thrust_chain)
    
    # 创建升级系统
    upgrade_system = CardUpgradeSystem()
    
    # 为刺击卡牌注册升级模板
    thrust_upgrades = [
        {
            "type": "damage_increase",
            "value": 2,
            "description": "伤害+2"
        },
        {
            "type": "ap_cost_reduction", 
            "value": 1,
            "description": "AP消耗-1"
        },
        {
            "type": "add_effect",
            "value": {"type": "emy_debuff", "buff_type": "pot", "stacks": 1, "duration": 2},
            "description": "添加中毒效果"
        }
    ]
    upgrade_system.register_upgrade_template("刺击", thrust_upgrades)
    
    return evolution_system, upgrade_system


# 示例使用
if __name__ == "__main__":
    # 这里可以添加测试代码
    print("卡牌升级与进化系统模块已加载")
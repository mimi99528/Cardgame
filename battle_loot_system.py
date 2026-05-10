"""
战斗掉落系统模块
负责敌人死亡后的物品、装备和卡牌掉落
"""
import random
from typing import List, Dict, Optional, Tuple
from models import Entity, Card
from inventory import Inventory, InventoryItem, ItemType, ItemShape
from config import Rarity, CardTag
from card_database import create_card_database


class BattleLootSystem:
    """战斗掉落系统"""
    
    def __init__(self):
        self.cards_db = create_card_database()
    
    def generate_loot(self, defeated_enemy: Entity, player_inventory: Inventory = None) -> Dict[str, List]:
        """
        生成战利品
        
        Args:
            defeated_enemy: 被击败的敌人实体
            player_inventory: 玩家背包（可选，用于自动放入物品）
            
        Returns:
            包含掉落物品的字典 {"items": [...], "equipments": [...], "cards": [...]}
        """
        loot = {
            "items": [],      # 普通物品
            "equipments": [], # 装备
            "cards": []       # 卡牌
        }
        
        # 1. 随机掉落物品或装备（50%概率）
        if random.random() < 0.5:
            item_or_equip = self._generate_item_or_equipment(defeated_enemy)
            if item_or_equip:
                if isinstance(item_or_equip, InventoryItem):
                    loot["items"].append(item_or_equip)
                    # 如果有背包，自动放入
                    if player_inventory:
                        success = player_inventory.add_item(item_or_equip)
                        if success:
                            print(f"[掉落] 物品 '{item_or_equip.name}' 已放入背包")
                        else:
                            print(f"[掉落] 物品 '{item_or_equip.name}' 背包已满！")
                else:
                    loot["equipments"].append(item_or_equip)
        
        # 2. 随机掉落卡牌（必定掉落3张）
        card_count = 3
        for _ in range(card_count):
            dropped_card = self._generate_card_drop(defeated_enemy)
            if dropped_card:
                loot["cards"].append(dropped_card)
        
        return loot
    
    def _generate_item_or_equipment(self, enemy: Entity) -> Optional[object]:
        """
        生成物品或装备掉落
        
        Returns:
            InventoryItem 或 Equipment 对象，或 None
        """
        # 简化实现：随机决定是物品还是装备
        if random.random() < 0.6:  # 60%概率是物品
            return self._generate_consumable_item(enemy)
        else:  # 40%概率是装备
            return self._generate_equipment_drop(enemy)
    
    def _generate_consumable_item(self, enemy: Entity) -> Optional[InventoryItem]:
        """生成消耗品掉落"""
        # 根据敌人类型决定掉落什么物品
        items_pool = [
            InventoryItem(
                name="生命药水",
                item_type=ItemType.CONSUMABLE,
                description="恢复5点生命值",
                weight=0.5,
                volume=1,
                shape=ItemShape.SINGLE,
                icon_color=(255, 100, 100),
                stackable=True,
                max_stack=5,
                use_effects={"heal": 5},
                ap_cost=1
            ),
            InventoryItem(
                name="治疗绷带",
                item_type=ItemType.CONSUMABLE,
                description="恢复3点生命值",
                weight=0.3,
                volume=1,
                shape=ItemShape.SINGLE,
                icon_color=(200, 200, 100),
                stackable=True,
                max_stack=3,
                use_effects={"heal": 3},
                ap_cost=1
            ),
            InventoryItem(
                name="能量药剂",
                item_type=ItemType.CONSUMABLE,
                description="恢复2点AP",
                weight=0.4,
                volume=1,
                shape=ItemShape.SINGLE,
                icon_color=(100, 100, 255),
                stackable=True,
                max_stack=3,
                use_effects={"restore_ap": 2},
                ap_cost=1
            ),
        ]
        
        return random.choice(items_pool).copy()
    
    def _generate_equipment_drop(self, enemy: Entity) -> Optional[object]:
        """生成装备掉落"""
        from models import Weapon, Armor
        
        # 简化实现：随机生成武器或防具
        if random.random() < 0.5:
            # 武器
            weapons = [
                Weapon(
                    name="生锈的剑",
                    description="一把老旧的剑",
                    rarity=Rarity.COMMON,
                    physical_bonus=8,
                    magical_bonus=0,
                    attack_modifier=0
                ),
                Weapon(
                    name="铁制匕首",
                    description="锋利的匕首",
                    rarity=Rarity.UNCOMMON,
                    physical_bonus=12,
                    magical_bonus=0,
                    attack_modifier=1
                ),
            ]
            return random.choice(weapons)
        else:
            # 防具
            armors = [
                Armor(
                    name="破旧皮甲",
                    description="磨损的皮甲",
                    rarity=Rarity.COMMON,
                    block_dice="1d4"
                ),
                Armor(
                    name="轻型护盾",
                    description="小型圆盾",
                    rarity=Rarity.UNCOMMON,
                    block_dice="1d6"
                ),
            ]
            return random.choice(armors)
    
    def _generate_card_drop(self, enemy: Entity) -> Optional[Card]:
        """
        生成卡牌掉落
        
        掉落规则：
        - 30%几率从全卡池抽
        - 20%几率掉落敌人卡组的卡牌（除了装备加进去的卡牌）
        - 50%机率根据职业标签抽选（加权随机）
        """
        # 第一步：决定卡牌来源
        source_roll = random.random()
        
        if source_roll < 0.3:
            # 30% 从全卡池抽取
            return self._draw_from_full_pool()
        elif source_roll < 0.5:
            # 20% 从敌人卡组抽取（排除装备卡牌）
            return self._draw_from_enemy_deck(enemy)
        else:
            # 50% 根据职业标签加权随机
            return self._draw_by_career_tags(enemy)
    
    def _draw_from_full_pool(self) -> Optional[Card]:
        """从全卡池随机抽取一张卡牌（排除装备赋予的卡牌）"""
        if not self.cards_db:
            return None
        
        # 过滤掉带有“赋予”标签的卡牌
        available_cards = [
            card for card in self.cards_db.values()
            if CardTag.EQUIPMENT_GRANTED not in card.tags
        ]
        
        if not available_cards:
            return None
        
        # 第二步：决定稀有度
        rarity = self._roll_rarity()
        
        # 第三步：从指定稀有度的卡池中抽取
        rarity_cards = [card for card in available_cards if card.rarity == rarity]
        
        if rarity_cards:
            selected_card = random.choice(rarity_cards)
            return selected_card.copy()
        
        # 如果该稀有度没有卡牌，降级抽取
        fallback_rarities = [Rarity.COMMON, Rarity.UNCOMMON, Rarity.RARE, Rarity.LEGENDARY]
        for r in fallback_rarities:
            fallback_cards = [card for card in available_cards if card.rarity == r]
            if fallback_cards:
                return random.choice(fallback_cards).copy()
        
        return None
    
    def _draw_from_enemy_deck(self, enemy: Entity) -> Optional[Card]:
        """
        从敌人卡组中抽取卡牌（排除装备提供的卡牌和带有“赋予”标签的卡牌）
        
        Args:
            enemy: 敌人实体
            
        Returns:
            抽取的卡牌副本
        """
        if not hasattr(enemy, 'deck') or not enemy.deck:
            return None
        
        # 获取装备提供的卡牌名称列表
        equipment_card_names = set()
        if hasattr(enemy, 'equipment_cards'):
            for equip_card in enemy.equipment_cards:
                equipment_card_names.add(equip_card.name)
        
        # 过滤掉装备提供的卡牌和带有“赋予”标签的卡牌
        non_equipment_cards = [
            card for card in enemy.deck 
            if card.name not in equipment_card_names
            and CardTag.EQUIPMENT_GRANTED not in card.tags
        ]
        
        if not non_equipment_cards:
            return None
        
        # 随机选择一张
        selected_card = random.choice(non_equipment_cards)
        return selected_card.copy()
    
    def _draw_by_career_tags(self, enemy: Entity) -> Optional[Card]:
        """
        根据职业标签加权随机抽取卡牌
        
        Args:
            enemy: 敌人实体
            
        Returns:
            抽取的卡牌副本
        """
        # 确定敌人的职业（如果有）
        enemy_career = None
        if hasattr(enemy, 'career') and enemy.career:
            enemy_career = enemy.career
        
        # 定义职业到标签的映射
        career_tag_weights = {
            "drifter": {  # 流浪者
                CardTag.MOVEMENT: 30,
                CardTag.EXPLORATION: 25,
                CardTag.SURVIVAL: 20,
                CardTag.UNIVERSAL: 15,
                CardTag.COMBAT: 10,
            },
            "artisan": {  # 手艺人
                CardTag.EQUIPMENT_INTERACT: 30,
                CardTag.BLOCK: 25,
                CardTag.BUFF: 20,
                CardTag.ENVIRONMENT: 15,
                CardTag.COMBAT: 10,
            },
            "pedlar": {  # 行商
                CardTag.SOCIAL: 30,
                CardTag.DISRUPT: 25,
                CardTag.LUCK: 20,
                CardTag.INTELLIGENCE: 15,
                CardTag.COMBAT: 10,
            },
            "farmer": {  # 农民
                CardTag.SURVIVAL: 30,
                CardTag.HEALING: 25,
                CardTag.AOE: 20,
                CardTag.STRENGTH: 15,
                CardTag.COMBAT: 10,
            },
            "scholar": {  # 学者
                CardTag.INTELLIGENCE: 30,
                CardTag.SPELL: 25,
                CardTag.KNOWLEDGE: 20,
                CardTag.BUFF: 15,
                CardTag.COMBAT: 10,
            },
        }
        
        # 默认标签权重（如果没有职业信息）
        default_weights = {
            CardTag.COMBAT: 40,
            CardTag.UNIVERSAL: 30,
            CardTag.MOVEMENT: 15,
            CardTag.HEALING: 15,
        }
        
        # 获取当前职业的标签权重
        if enemy_career:
            career_key = enemy_career.career_type.value.lower()
            tag_weights = career_tag_weights.get(career_key, default_weights)
        else:
            tag_weights = default_weights
        
        # 构建加权卡池（排除带有“赋予”标签的卡牌）
        weighted_cards = []
        for card in self.cards_db.values():
            # 跳过带有“赋予”标签的卡牌
            if CardTag.EQUIPMENT_GRANTED in card.tags:
                continue
            
            # 计算卡牌的总权重
            card_weight = 0
            for tag, weight in tag_weights.items():
                if tag in card.tags:
                    card_weight += weight
            
            # 如果卡牌有匹配的标签，加入卡池
            if card_weight > 0:
                weighted_cards.append((card, card_weight))
        
        if not weighted_cards:
            # 如果没有匹配的卡牌，从全卡池抽取
            return self._draw_from_full_pool()
        
        # 加权随机选择
        total_weight = sum(weight for _, weight in weighted_cards)
        roll = random.uniform(0, total_weight)
        
        current_weight = 0
        for card, weight in weighted_cards:
            current_weight += weight
            if roll <= current_weight:
                # 第二步：决定稀有度（可以重新roll，也可以保持原稀有度）
                # 这里选择保持原稀有度，因为已经按标签筛选了
                return card.copy()
        
        # 不应该到达这里
        return weighted_cards[-1][0].copy() if weighted_cards else None
    
    def _roll_rarity(self) -> Rarity:
        """
        决定稀有度
        
        稀有度概率：
        - 普通 (Common): 12/20 = 60%
        - 优秀 (Uncommon): 5/20 = 25%
        - 稀有 (Rare): 2/20 = 10%
        - 传说 (Legendary): 1/20 = 5%
        """
        roll = random.randint(1, 20)
        
        if roll <= 12:
            return Rarity.COMMON
        elif roll <= 17:
            return Rarity.UNCOMMON
        elif roll <= 19:
            return Rarity.RARE
        else:
            return Rarity.LEGENDARY
    
    def format_loot_message(self, loot: Dict[str, List]) -> str:
        """
        格式化掉落信息为可读字符串
        
        Args:
            loot: 掉落物品字典
            
        Returns:
            格式化的掉落信息
        """
        messages = []
        
        if loot["items"]:
            item_names = [item.name for item in loot["items"]]
            messages.append(f"获得物品: {', '.join(item_names)}")
        
        if loot["equipments"]:
            equip_names = [equip.name for equip in loot["equipments"]]
            messages.append(f"获得装备: {', '.join(equip_names)}")
        
        if loot["cards"]:
            card_names = [card.name for card in loot["cards"]]
            messages.append(f"获得卡牌: {', '.join(card_names)}")
        
        if not messages:
            messages.append("没有获得任何战利品")
        
        return "\n".join(messages)

"""
核心数据模型模块
包含实体、卡牌、装备等基础类
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from copy import deepcopy
from enum import Enum
import random

from config import Rarity, CardType, BuffType, CONSTANTS, TargetType


# 控制类型枚举
class ControlType(Enum):
    PLAYER = "player"  # 玩家控制
    AI = "ai"          # AI控制


@dataclass
class Stats:
    """角色六维属性"""
    strength: int = 14    # 力量
    dexterity: int = 14   # 敏捷
    constitution: int = 10  # 耐力
    intelligence: int = 8   # 智力
    wisdom: int = 14      # 感知
    charisma: int = 8     # 魅力
    
    def get_modifier(self, stat_name: str) -> int:
        """获取属性修正值"""
        value = getattr(self, stat_name, 10)
        return (value - 10) // 2


@dataclass
class Equipment:
    """装备基类"""
    name: str
    description: str
    rarity: Rarity
    
    def __str__(self):
        return self.name


@dataclass
class Weapon(Equipment):
    """武器类"""
    physical_bonus: int = 0  # 物理攻击加成
    magical_bonus: int = 0   # 魔法攻击加成
    
    def get_bonus(self, damage_type: str) -> int:
        """根据伤害类型获取加成"""
        if damage_type == "phy":
            return self.physical_bonus
        elif damage_type == "mag":
            return self.magical_bonus
        return 0


@dataclass
class Armor(Equipment):
    """防具类"""
    block_value: int = 0  # 格挡值


@dataclass
class Buff:
    """Buff/Debuff 效果"""
    buff_type: BuffType
    stacks: int  # 层数
    duration: int = -1  # 持续回合数，-1表示永久
    
    def tick(self) -> bool:
        """更新持续时间，返回是否应该移除"""
        if self.duration > 0:
            self.duration -= 1
            return self.duration <= 0
        return False


class Entity:
    """游戏实体基类（角色、敌人等）"""
    
    def __init__(
        self,
        name: str,
        max_hp: int,
        max_ap: int,
        equipment: Dict[str, Equipment],
        cards: List['Card'],
        hand_size: int = CONSTANTS.DEFAULT_HAND_SIZE,
        stats: Optional[Stats] = None,
        control_type: 'ControlType' = None,
        position: Optional[Tuple[int, int]] = None,
        max_md: int = 30,  # 默认移动距离30尺（6格）
        permanent_cards: Optional[List['Card']] = None  # 常驻卡牌列表
    ):
        # 基础属性
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.max_ap = max_ap
        self.ap = max_ap
        
        # 移动距离
        self.max_md = max_md
        self.md = max_md
        
        # 战斗相关
        self.block = 0
        self.hand_size = hand_size
        self.hand: List[Card] = []
        self.deck: List[Card] = []
        
        # 常驻卡牌（不参与抽牌）
        self.permanent_cards: List[Card] = permanent_cards or []
        for card in self.permanent_cards:
            card.owner = self
        
        # 装备
        self.equipment = equipment
        
        # 属性
        self.stats = stats or Stats()
        
        # Buffs
        self.buffs: Dict[str, Buff] = {}
        
        # 控制类型和位置
        from models import ControlType
        self.control_type = control_type or ControlType.AI
        self.position = position or (0, 0)
        
        # 初始化卡组
        self._initialize_deck(cards)
    
    def _initialize_deck(self, cards: List['Card']):
        """初始化卡组并设置所有者"""
        self.deck = [card.copy() for card in cards]
        for card in self.deck:
            card.owner = self
    
    def reset_for_battle(self):
        """重置状态准备战斗"""
        self.hp = self.max_hp
        self.ap = self.max_ap
        self.md = self.max_md
        self.block = 0
        self.buffs.clear()
        self.hand.clear()
        # 将常驻卡牌加入手牌
        for card in self.permanent_cards:
            if card not in self.hand:
                self.hand.append(card)
        return self
    
    def draw_hand(self):
        """抽手牌（不包括常驻卡牌）"""
        # 先保留常驻卡牌
        permanent_in_hand = [card for card in self.hand if card in self.permanent_cards]
        
        # 从卡组中抽取非常驻卡牌
        available_cards = [c for c in self.deck if c not in self.permanent_cards]
        
        # 计算需要抽取的数量（总手牌数 - 常驻卡牌数）
        # 常驻卡牌不占用普通手牌上限
        cards_to_draw = self.hand_size - len(permanent_in_hand)
        
        if cards_to_draw <= 0:
            # 如果常驻卡牌已经填满或超过手牌数，只保留常驻卡牌
            self.hand = permanent_in_hand[:self.hand_size]
        elif len(available_cards) >= cards_to_draw:
            # 抽取足够的卡牌
            drawn_cards = random.sample(available_cards, cards_to_draw)
            self.hand = permanent_in_hand + drawn_cards
        else:
            # 如果卡组不够，抽所有可用的
            self.hand = permanent_in_hand + available_cards
        
        # 确保所有常驻卡牌都在手牌中（即使超过hand_size）
        for perm_card in self.permanent_cards:
            if perm_card not in self.hand:
                # 直接添加常驻卡牌，不占用普通手牌空间
                self.hand.append(perm_card)
    
    def play_card(self, card: 'Card', target: 'Entity') -> tuple:
        """
        打出卡牌
        
        Returns:
            tuple: (success: bool, is_permanent: bool)
        """
        if card not in self.hand:
            return False, False
        
        if self.ap < card.ap_cost:
            return False, False
        
        # 检查是否是常驻卡牌
        is_permanent = card in self.permanent_cards
        
        # 扣除AP
        self.ap -= card.ap_cost
        
        # 从手牌移除
        self.hand.remove(card)
        
        # 应用卡牌效果
        card.apply_effects(target)
        
        # 如果是常驻卡牌，立即重新加入手牌（会自动触发上升动画）
        if is_permanent:
            self.hand.append(card)
            # 返回一个标记，表示这是常驻卡牌被重新加入
            return True, True
        
        return True, False
    
    def take_damage(self, damage: int):
        """受到伤害"""
        # 先消耗格挡
        if self.block > 0:
            if self.block >= damage:
                self.block -= damage
                damage = 0
            else:
                damage -= self.block
                self.block = 0
        
        # 扣除HP
        self.hp -= damage
    
    def heal(self, amount: int):
        """治疗"""
        self.hp = min(self.hp + amount, self.max_hp)
    
    def add_block(self, amount: int):
        """增加格挡"""
        self.block += amount
        max_block = int(self.max_hp * CONSTANTS.MAX_BLOCK_RATIO)
        self.block = min(self.block, max_block)
    
    def apply_buff(self, buff: Buff):
        """应用Buff"""
        key = f"{buff.buff_type.value}_{buff.stacks}"
        self.buffs[key] = buff
    
    def process_buffs(self) -> List[str]:
        """处理所有Buff，返回效果描述列表"""
        effects = []
        buffs_to_remove = []
        
        for key, buff in self.buffs.items():
            if buff.buff_type == BuffType.POISON:
                # 中毒效果：每层造成5%最大HP的伤害
                damage = int(self.max_hp * 0.05 * buff.stacks)
                self.take_damage(damage)
                effects.append(f"{self.name}毒发，受到{damage}点伤害")
            
            # 检查是否需要移除
            if buff.tick():
                buffs_to_remove.append(key)
        
        # 移除过期Buff
        for key in buffs_to_remove:
            del self.buffs[key]
        
        return effects
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.hp > 0
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"Entity({self.name}, HP:{self.hp}/{self.max_hp})"


class Card:
    """卡牌类"""
    
    def __init__(
        self,
        name: str,
        card_type: CardType,
        ap_cost: int,
        effects: Dict[str, any],
        description: str,
        rarity: Rarity = Rarity.COMMON,
        atk_dis: int = 1,
        atk_rnge: Optional[Dict[str, any]] = None,
        target_type: TargetType = TargetType.ENEMY,
        is_movement: bool = False  # 是否为移动卡牌
    ):
        self.name = name
        self.card_type = card_type
        self.ap_cost = ap_cost
        self.effects = effects
        self.description = description
        self.rarity = rarity
        self.owner: Optional[Entity] = None
        self.atk_dis = atk_dis  # 攻击距离，默认为1（近战）
        self.atk_rnge = atk_rnge or {"type": "circle", "radius": 1}  # 攻击范围，默认为半径1的圆形
        self.target_type = target_type  # 目标类型，默认为敌人
        self.is_movement = is_movement  # 是否为移动卡牌
    
    def apply_effects(self, target: Entity):
        """应用卡牌效果"""
        if not self.owner:
            raise ValueError("卡牌没有所有者")
        
        attacker = self.owner
        results = []
        
        # 伤害效果
        if "hp" in self.effects:
            damage = self.effects["hp"]
            
            # 获取武器加成
            weapon = attacker.equipment.get("weapon")
            if weapon:
                damage_type = self.card_type.value.split("_")[-1] if "_" in self.card_type.value else "phy"
                bonus = weapon.get_bonus(damage_type)
                damage -= bonus
            
            damage_abs = abs(damage)
            results.append(f"{attacker}对{target}使用{self.name}，造成{damage_abs}点伤害")
            
            target.take_damage(damage_abs)
        
        # 格挡效果
        if "block" in self.effects:
            block_amount = self.effects["block"]
            attacker.add_block(block_amount)
            results.append(f"{attacker}使用{self.name}，获得{block_amount}点格挡")
        
        # Buff效果
        for effect_key, effect_value in self.effects.items():
            # 检查是否是Buff
            for buff_type in BuffType:
                if effect_key.startswith(buff_type.value):
                    try:
                        stacks = int(effect_key.split("_")[1]) if "_" in effect_key else 1
                    except (IndexError, ValueError):
                        stacks = 1
                    
                    buff = Buff(buff_type=buff_type, stacks=effect_value)
                    
                    # 判断是给自己还是给目标
                    if effect_key in ["pot_1", "pot_2", "pot_3"]:  # Debuff
                        target.apply_buff(buff)
                        results.append(f"{attacker}对{target}施加了{effect_value}层{buff_type.name}")
                    else:  # Buff
                        attacker.apply_buff(buff)
                        results.append(f"{attacker}获得了{effect_value}层{buff_type.name}")
        
        return results
    
    def copy(self) -> 'Card':
        """创建卡牌副本"""
        new_card = Card(
            name=self.name,
            card_type=self.card_type,
            ap_cost=self.ap_cost,
            effects=deepcopy(self.effects),
            description=self.description,
            rarity=self.rarity,
            atk_dis=self.atk_dis,
            atk_rnge=deepcopy(self.atk_rnge),
            target_type=self.target_type,
            is_movement=self.is_movement
        )
        return new_card
    
    def __str__(self):
        return f"[{self.name}] ({self.card_type.name}, AP:{self.ap_cost})"
    
    def __repr__(self):
        return self.__str__()

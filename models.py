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
from inventory import Inventory
from equipment_manager import EquipmentManager


def roll_dice_sum_from_expression(dice_expr: str) -> int:
    """
    从骰子表达式掷骰并返回总和
    
    Args:
        dice_expr: 骰子表达式，如 "2d2", "2d3", "1d4" 等
        
    Returns:
        骰子结果的总和
    """
    from dice_system import roll_dice_sum
    
    try:
        # 解析表达式，格式为 "NdM"
        parts = dice_expr.lower().split('d')
        if len(parts) == 2:
            num_dice = int(parts[0])
            sides = int(parts[1])
            return roll_dice_sum(num_dice, sides)
        else:
            return 0
    except (ValueError, IndexError):
        return 0


# 控制类型枚举
class ControlType(Enum):
    PLAYER = "player"  # 玩家控制
    AI = "ai"          # AI控制


@dataclass
class Stats:
    """角色四维属性，两维资源，一维隐藏"""
    # 基础属性
    strength: int = 10    # 力量
    dexterity: int = 10   # 敏捷
    intelligence: int = 10   # 心智
    charisma: int = 10     # 魅力
    luck: float = 10
    
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
    # 装备提供的卡牌列表（名称）
    provided_cards: List[str] = field(default_factory=list)
    # 每回合提供的格挡值
    block_per_turn: int = 0
    # AP加成（护甲专用）
    ap_bonus: int = 0
    
    def __str__(self):
        return self.name


@dataclass
class Weapon(Equipment):
    """武器类"""
    physical_bonus: int = 0  # 物理攻击加成
    magical_bonus: int = 0   # 魔法攻击加成
    # 攻击加值（用于2d10+加值的判定）
    attack_modifier: int = 0
    
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
    block_value: int = 0  # 基础格挡值（已废弃，使用block_dice）
    block_dice: str = ""  # 格挡骰子表达式，如 "2d2", "2d3", "2d4"
    # AC（护甲等级）计算公式相关：敏捷*2 + 力量*1，每超过30点增加1AC
    # ac_bonus 已经在父类中定义
    
    def calculate_ac_bonus(self, stats: Stats) -> int:
        """根据属性计算AC加成"""
        attribute_score = stats.dexterity * 2 + stats.strength * 1
        if attribute_score > 30:
            return (attribute_score - 30) // 3
        return 0
    
    def roll_block(self) -> int:
        """掷格挡骰子"""
        if self.block_dice:
            return roll_dice_sum_from_expression(self.block_dice)
        return self.block_value


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
        permanent_cards: Optional[List['Card']] = None,  # 常驻卡牌列表
        inventory: Optional[Inventory] = None  # 背包系统
    ):
        # 基础属性
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        
        # 装备（需要先设置，因为AP计算需要）
        self.equipment = equipment
        
        # 计算初始AP（包括护甲加成）
        self.base_max_ap = max_ap
        self.stats = stats or Stats()
        self.max_ap = self._calculate_max_ap()
        self.ap = self.max_ap
        
        # 移动距离
        self.max_md = max_md
        self.md = max_md
        
        # 战斗相关
        self.block = 0
        self.hand_size = hand_size
        self.hand: List[Card] = []
        self.deck: List[Card] = []
        self.discard_pile: List[Card] = []  # 弃牌堆
        
        # 常驻卡牌（不参与抽牌）
        self.permanent_cards: List[Card] = permanent_cards or []
        for card in self.permanent_cards:
            card.owner = self
        
        # 装备提供的卡牌（每回合加入手牌）
        self.equipment_cards: List[Card] = []
        
        # Buffs
        self.buffs: Dict[str, Buff] = {}
        
        # 控制类型和位置
        from models import ControlType
        self.control_type = control_type or ControlType.AI
        self.position = position or (0, 0)
        
        # 初始化卡组
        self._initialize_deck(cards)
        
        # 加载装备提供的卡牌
        self._load_equipment_cards()
        
        # 初始化背包系统
        self.inventory = inventory or Inventory(owner_name=name)
        
        # 初始化装备管理器
        self.equipment_manager = EquipmentManager(owner_name=name)
    
    def _calculate_max_ap(self) -> int:
        """计算最大AP（包括护甲AC加成）"""
        ap = self.base_max_ap
        armor = self.equipment.get("armor")
        # if armor and isinstance(armor, Armor):
        #     ap += armor.calculate_ac_bonus(self.stats)
        return ap
    
    def _load_equipment_cards(self):
        """从装备加载提供的卡牌"""
        from card_database import create_card_database
        
        cards_db = create_card_database()
        self.equipment_cards.clear()
        
        # 遍历所有装备
        for equip_slot, equipment in self.equipment.items():
            if equipment and hasattr(equipment, 'provided_cards'):
                for card_name in equipment.provided_cards:
                    if card_name in cards_db:
                        # 创建卡牌副本并设置所有者
                        card = cards_db[card_name].copy()
                        card.owner = self
                        self.equipment_cards.append(card)
    
    def _initialize_deck(self, cards: List['Card']):
        """初始化卡组并设置所有者"""
        self.deck = [card.copy() for card in cards]
        for card in self.deck:
            card.owner = self
        self.discard_pile = []  # 初始化弃牌堆为空
    
    def reset_for_battle(self):
        """重置状态准备战斗"""
        self.hp = self.max_hp
        self.ap = self.max_ap
        self.md = self.max_md
        self.block = 0
        self.buffs.clear()
        self.hand.clear()
        self.discard_pile.clear()  # 清空弃牌堆
        
        # 将常驻卡牌加入手牌
        for card in self.permanent_cards:
            if card not in self.hand:
                self.hand.append(card)
        
        # 加载装备卡牌
        self._load_equipment_cards()
        
        # 初始抽4张牌（防止一开始没牌打）
        import random
        initial_draw_count = 4
        available_cards = [c for c in self.deck if c not in self.permanent_cards]
        
        if len(available_cards) >= initial_draw_count:
            drawn_cards = random.sample(available_cards, initial_draw_count)
            for card in drawn_cards:
                self.deck.remove(card)
                self.hand.append(card)
        else:
            # 如果卡组不够，抽所有可用的
            for card in available_cards:
                self.deck.remove(card)
                self.hand.append(card)
        
        print(f"[DEBUG] {self.name} 战斗开始初始抽牌: 从卡组抽取{min(initial_draw_count, len(available_cards))}张")
        
        return self
    
    def draw_hand(self):
        """抽手牌（不包括常驻卡牌）"""
        # 先保留常驻卡牌
        permanent_in_hand = [card for card in self.hand if card in self.permanent_cards]
        
        # 保留上一回合的普通卡牌和装备卡牌
        non_permanent_in_hand = [card for card in self.hand if card not in self.permanent_cards]
        
        print(f"[DEBUG] {self.name} draw_hand: hand_size={len(self.hand)}, permanent={len(permanent_in_hand)}, non_permanent={len(non_permanent_in_hand)}, equipment={len(self.equipment_cards)}")
        
        # 每回合固定抽2张牌
        cards_to_draw = 2
        
        print(f"[DEBUG] {self.name} cards_to_draw={cards_to_draw}, deck={len(self.deck)}, discard={len(self.discard_pile)}")
        
        # 检查卡组中的可用卡牌数量
        available_cards = [c for c in self.deck if c not in self.permanent_cards]
        
        # 如果卡组中的卡牌不足，立即从弃牌堆洗牌补充
        if len(available_cards) < cards_to_draw and len(self.discard_pile) > 0:
            # 将弃牌堆洗入卡组
            self.deck.extend(self.discard_pile)
            random.shuffle(self.deck)
            self.discard_pile.clear()
            # 重新获取可用卡牌
            available_cards = [c for c in self.deck if c not in self.permanent_cards]
        
        # 抽牌逻辑
        drawn_cards = []
        if len(available_cards) >= cards_to_draw:
            # 抽取足够的卡牌
            drawn_cards = random.sample(available_cards, cards_to_draw)
            # 从卡组中移除已抽的卡牌
            for card in drawn_cards:
                self.deck.remove(card)
        else:
            # 如果卡组仍然不够，抽所有可用的
            drawn_cards = available_cards[:]
            for card in drawn_cards:
                self.deck.remove(card)
        
        # 新手牌 = 上一回合保留的卡牌 + 新抽的卡牌 + 常驻卡牌 + 装备卡牌
        self.hand = non_permanent_in_hand + drawn_cards
        
        # 确保所有常驻卡牌都在手牌中（即使超过hand_size）
        for perm_card in self.permanent_cards:
            if perm_card not in self.hand:
                # 直接添加常驻卡牌，不占用普通手牌空间
                self.hand.append(perm_card)
        
        # 确保所有装备卡牌都在手牌中
        for equip_card in self.equipment_cards:
            if equip_card not in self.hand:
                self.hand.append(equip_card)
        
        # 限制手牌上限（只计算非永久卡牌）
        non_perm_cards = [c for c in self.hand if c not in self.permanent_cards and c not in self.equipment_cards]
        if len(non_perm_cards) > self.hand_size:
            # 移除多余的卡牌（保留前面的）
            excess = len(non_perm_cards) - self.hand_size
            # 从后往前移除
            for i in range(len(self.hand) - 1, -1, -1):
                if self.hand[i] not in self.permanent_cards and self.hand[i] not in self.equipment_cards:
                    # 这张卡牌移回弃牌堆
                    self.discard_pile.append(self.hand.pop(i))
                    excess -= 1
                    if excess <= 0:
                        break
        
        print(f"[DEBUG] {self.name} draw_hand结束: hand_size={len(self.hand)}, deck={len(self.deck)}, discard={len(self.discard_pile)}")
    
    def play_card(self, card: 'Card', target: 'Entity') -> tuple:
        """
        打出卡牌
        
        Returns:
            tuple: (success: bool, is_permanent: bool, log_entries: List)
        """
        if card not in self.hand:
            return False, False, []
        
        if self.ap < card.ap_cost:
            return False, False, []
        
        # 检查是否是常驻卡牌
        is_permanent = card in self.permanent_cards
        
        # 扣除AP
        self.ap -= card.ap_cost
        
        # 从手牌移除
        self.hand.remove(card)
        
        # 应用卡牌效果并获取日志
        log_entries = card.apply_effects(target)
        
        # 如果是常驻卡牌，立即重新加入手牌（会自动触发上升动画）
        if is_permanent:
            self.hand.append(card)
            # 返回一个标记，表示这是常驻卡牌被重新加入
            return True, True, log_entries
        
        # 非常驻卡牌进入弃牌堆
        self.discard_pile.append(card)
        
        return True, False, log_entries
    
    def take_damage(self, damage: int, ignore_block: bool = False):
        """
        受到伤害
        
        Args:
            damage: 伤害值
            ignore_block: 是否忽略格挡(真伤)
        """
        # 如果不忽略格挡，先消耗格挡
        if not ignore_block and self.block > 0:
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
        """应用Buff，支持同种buff不同层数叠加"""
        key = buff.buff_type.value  # 只使用buff类型作为key
        
        if key in self.buffs:
            # 如果已存在同种buff，叠加层数
            existing_buff = self.buffs[key]
            existing_buff.stacks += buff.stacks
            # 更新持续时间（取最大值）
            if buff.duration > 0:
                if existing_buff.duration < 0:
                    existing_buff.duration = buff.duration
                else:
                    existing_buff.duration = max(existing_buff.duration, buff.duration)
        else:
            # 新的buff类型，直接添加
            self.buffs[key] = buff
    
    def process_buffs(self) -> List[str]:
        """处理所有Buff，返回效果描述列表"""
        effects = []
        buffs_to_remove = []
        
        for key, buff in self.buffs.items():
            if buff.buff_type == BuffType.POISON:
                # 中毒效果：每x层毒每回合造成1dx+x//2的伤害（真伤，忽略格挡）
                from dice_system import roll_dice_sum
                stacks = buff.stacks
                # 掷1dx骰子
                dice_damage = roll_dice_sum(1, stacks) if stacks > 0 else 0
                # 加上 x//2
                additional_damage = stacks // 2
                total_damage = dice_damage + additional_damage
                
                # 使用真伤（忽略格挡）
                self.take_damage(total_damage, ignore_block=True)
                effects.append(f"{self.name}毒发，受到{total_damage}点真实伤害（1d{stacks}+{additional_damage}）")
            
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
    
    def get_deck_info(self) -> dict:
        """获取卡组和弃牌堆信息"""
        return {
            'deck_count': len(self.deck),
            'discard_count': len(self.discard_pile),
            'hand_count': len([c for c in self.hand if c not in self.permanent_cards and c not in self.equipment_cards])
        }
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"Entity({self.name}, HP:{self.hp}/{self.max_hp})"


@dataclass
class Card:
    """卡牌类"""
    
    # 类变量：用于生成唯一ID的计数器
    _id_counter = 0
    
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
        is_movement: bool = False,  # 是否为移动卡牌
        card_id: Optional[int] = None  # 卡牌唯一ID（可选，自动生成）
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
        
        # 分配唯一ID
        if card_id is not None:
            self.card_id = card_id
        else:
            Card._id_counter += 1
            self.card_id = Card._id_counter
    
    def _apply_damage_effect(self, attacker: Entity, target: Entity, base_damage: int, card_name: str) -> List:
        """
        应用伤害效果（统一的攻击判定逻辑）
        
        Args:
            attacker: 攻击者
            target: 目标
            base_damage: 基础伤害
            card_name: 卡牌名称
            
        Returns:
            日志消息列表 (message, level, color_key)
        """
        results = []
        
        # 获取武器
        weapon = attacker.equipment.get("weapon")
        
        # 执行攻击判定
        from attack_system import perform_attack_check, AttackOutcome
        attack_result = perform_attack_check(attacker, target, base_damage, weapon)
        
        # 根据攻击结果确定颜色键值
        outcome_color_map = {
            AttackOutcome.CRITICAL_SUCCESS: "critical_success",
            AttackOutcome.SUCCESS: "success",
            AttackOutcome.PARTIAL_SUCCESS: "partial_success",
            AttackOutcome.FAILURE: "failure",
            AttackOutcome.CRITICAL_FAILURE: "critical_failure"
        }
        color_key = outcome_color_map.get(attack_result.outcome, "normal")
        
        # 记录判定结果
        results.append((f"{attacker}对{target}使用{card_name}", 0, color_key))  # level 0
        
        # 详细判定信息（level 2 - verbose）
        results.append((f"  判定: {attack_result.outcome.value}", 2, color_key))
        results.append((f"  骰子: {attack_result.dice_results[0]} + {attack_result.dice_results[1]} = {attack_result.total_roll}", 2, color_key))
        results.append((f"  最终结果: {attack_result.final_result} vs DN {attack_result.difficulty}", 2, color_key))
        
        # 应用实际伤害
        if attack_result.actual_damage > 0:
            target.take_damage(attack_result.actual_damage)
            results.append((f"  造成{attack_result.actual_damage}点伤害", 1, color_key))  # level 1
        else:
            results.append((f"  未命中", 1, color_key))  # level 1
        
        # 处理额外效果
        if attack_result.extra_effects:
            for extra_effect in attack_result.extra_effects:
                results.append((f"  额外效果: {extra_effect}", 2, color_key))  # level 2
        
        return results
    
    def apply_effects(self, target: Entity):
        """应用卡牌效果"""
        if not self.owner:
            raise ValueError("卡牌没有所有者")
        
        attacker = self.owner
        results = []
        
        # 处理结构化效果列表
        if isinstance(self.effects, list):
            for effect in self.effects:
                effect_type = effect.get("type", "")
                
                # 敌方伤害效果 - 使用骰子表达式
                if effect_type == "emy_dmg":
                    dice_expr = effect.get("dice", "")
                    if dice_expr:
                        # 解析骰子表达式并掷骰
                        base_damage = self._roll_dice_expression(dice_expr)
                        
                        # 使用统一的伤害处理逻辑
                        results.extend(self._apply_damage_effect(attacker, target, base_damage, self.name))
                
                # 自我治疗
                elif effect_type == "self_heal":
                    amount = effect.get("amount", 0)
                    attacker.heal(amount)
                    results.append((f"{attacker}使用{self.name}，恢复{amount}点生命值", 0, "success"))  # level 0, success color
                
                # 自我格挡 - 使用骰子表达式
                elif effect_type == "self_block":
                    dice_expr = effect.get("dice", "")
                    if dice_expr:
                        block_amount = self._roll_dice_expression(dice_expr)
                    else:
                        block_amount = effect.get("amount", 0)
                    attacker.add_block(block_amount)
                    results.append((f"{attacker}使用{self.name}，获得{block_amount}点格挡", 0, "success"))  # level 0, success color
                
                # 敌方Debuff
                elif effect_type == "emy_debuff":
                    buff_type_str = effect.get("buff_type", "")
                    stacks = effect.get("stacks", 1)
                    duration = effect.get("duration", -1)
                    
                    # 查找对应的BuffType
                    for bt in BuffType:
                        if bt.value == buff_type_str:
                            buff = Buff(buff_type=bt, stacks=stacks, duration=duration)
                            target.apply_buff(buff)
                            results.append((f"{attacker}对{target}施加了{stacks}层{bt.name}", 0, "failure"))  # level 0, failure color
                            break
                
                # 自我Buff
                elif effect_type == "self_buff":
                    buff_type_str = effect.get("buff_type", "")
                    stacks = effect.get("stacks", 1)
                    duration = effect.get("duration", -1)
                    
                    # 查找对应的BuffType
                    for bt in BuffType:
                        if bt.value == buff_type_str:
                            buff = Buff(buff_type=bt, stacks=stacks, duration=duration)
                            attacker.apply_buff(buff)
                            results.append((f"{attacker}获得了{stacks}层{bt.name}", 0, "success"))  # level 0, success color
                            break
        
        # 兼容旧版字典格式effects
        elif isinstance(self.effects, dict):
            # 伤害效果 - 使用新的攻击判定系统
            if "hp" in self.effects:
                base_damage = abs(self.effects["hp"])
                
                # 使用统一的伤害处理逻辑
                results.extend(self._apply_damage_effect(attacker, target, base_damage, self.name))
            
            # 骰子伤害效果（新格式）
            elif "hp_dice" in self.effects:
                dice_expr = self.effects["hp_dice"]
                base_damage = self._roll_dice_expression(dice_expr)
                
                # 使用统一的伤害处理逻辑
                results.extend(self._apply_damage_effect(attacker, target, base_damage, self.name))
            
            # 格挡效果
            if "block" in self.effects:
                block_amount = self.effects["block"]
                attacker.add_block(block_amount)
                results.append((f"{attacker}使用{self.name}，获得{block_amount}点格挡", 0, "success"))  # level 0, success color
            
            # 骰子格挡效果（新格式）
            if "block_dice" in self.effects:
                dice_expr = self.effects["block_dice"]
                block_amount = self._roll_dice_expression(dice_expr)
                attacker.add_block(block_amount)
                results.append((f"{attacker}使用{self.name}，获得{block_amount}点格挡", 0, "success"))  # level 0, success color
            
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
                            results.append((f"{attacker}对{target}施加了{effect_value}层{buff_type.name}", 0, "failure"))  # level 0, failure color
                        else:  # Buff
                            attacker.apply_buff(buff)
                            results.append((f"{attacker}获得了{effect_value}层{buff_type.name}", 0, "success"))  # level 0, success color
        
        return results
    
    def _roll_dice_expression(self, dice_expr: str) -> int:
        """
        解析并掷骰子表达式
        
        Args:
            dice_expr: 骰子表达式，如 "1d4", "2d6", "3d8", "d2", "d6" 等
            
        Returns:
            骰子结果的总和
        """
        from dice_system import roll_dice_sum
        
        try:
            # 解析表达式，格式为 "NdM" 或 "dM"
            dice_expr = dice_expr.lower().strip()
            
            if 'd' in dice_expr:
                parts = dice_expr.split('d')
                
                if len(parts) == 2:
                    # 处理 "NdM" 或 "dM" 格式
                    num_dice = int(parts[0]) if parts[0] else 1  # 如果前面为空，默认为1
                    sides = int(parts[1])
                    return roll_dice_sum(num_dice, sides)
            
            # 如果格式不正确，尝试直接转换为整数
            return int(dice_expr)
        except (ValueError, IndexError):
            return 0
    
    def copy(self) -> 'Card':
        """创建卡牌副本（不保留原ID，生成新ID）"""
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
            # 不传递card_id，让副本获得新的唯一ID
        )
        return new_card
    
    def __str__(self):
        return f"[{self.name}] (ID:{self.card_id}, {self.card_type.name}, AP:{self.ap_cost})"
    
    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        """使Card可哈希，用于集合和字典键（基于唯一ID）"""
        return hash(self.card_id)
    
    def is_samename(self, other):
        """比较两个卡牌是否同名（内容相同但可能是不同实例）"""
        if not isinstance(other, Card):
            return False
        return (self.name == other.name and 
                self.card_type == other.card_type and
                self.ap_cost == other.ap_cost)

    def __eq__(self, other):
        """比较两个卡牌是否是同一个实例（基于唯一ID）"""
        if not isinstance(other, Card):
            return False
        return self.card_id == other.card_id

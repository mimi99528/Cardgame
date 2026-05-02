"""
卡牌数据库模块
定义所有可用的卡牌、武器和防具
"""
from models import Card, Weapon, Armor, Stats, ControlType
from config import Rarity, CardType, TargetType


# ==================== 卡牌数据库 ====================

def create_card_database():
    """创建卡牌数据库"""
    cards = {
        # 测试卡牌
        "instant_kill": Card(
            name="秒杀",
            card_type=CardType.ATTACK_PHYSICAL,
            ap_cost=3,
            effects={"hp": -999999},
            description="隐藏测试卡牌：秒杀",
            rarity=Rarity.LEGENDARY
        ),
        
        "basic_attack": Card(
            name="普攻",
            card_type=CardType.ATTACK_PHYSICAL,
            ap_cost=1,
            effects={"hp": -10},
            description="基础物理攻击",
            rarity=Rarity.COMMON
        ),
        
        "serious_strike": Card(
            name="认真一击",
            card_type=CardType.ATTACK_PHYSICAL,
            ap_cost=2,
            effects={"hp": -25},
            description="强力的物理攻击",
            rarity=Rarity.UNCOMMON
        ),
        
        "block": Card(
            name="格挡",
            card_type=CardType.BLOCK,
            ap_cost=1,
            effects={"block": 25},
            description="获得25点格挡值",
            rarity=Rarity.COMMON,
            target_type=TargetType.SELF
        ),
        
        "poison": Card(
            name="投毒",
            card_type=CardType.BUFF,
            ap_cost=1,
            effects={"pot_3": 3},
            description="对敌人施加3层中毒效果",
            rarity=Rarity.RARE
        ),
        
        "heal": Card(
            name="治疗",
            card_type=CardType.HEAL,
            ap_cost=2,
            effects={"hp": 30},  # 正数表示治疗
            description="恢复30点生命值",
            rarity=Rarity.UNCOMMON,
            target_type=TargetType.SELF
        ),
        
        "fireball": Card(
            name="火球术",
            card_type=CardType.ATTACK_MAGICAL,
            ap_cost=2,
            effects={"hp": -20},
            description="发射火球造成魔法伤害",
            rarity=Rarity.UNCOMMON
        ),
        
        "shield": Card(
            name="护盾",
            card_type=CardType.BLOCK,
            ap_cost=2,
            effects={"block": 40},
            description="获得40点格挡值",
            rarity=Rarity.RARE,
            target_type=TargetType.SELF
        ),
    }
    
    return cards


# ==================== 武器数据库 ====================

def create_weapon_database():
    """创建武器数据库"""
    weapons = {
        "none": Weapon(
            name="",
            description="",
            rarity=Rarity.COMMON,
            physical_bonus=0,
            magical_bonus=0
        ),
        
        "wooden_sword": Weapon(
            name="训练木剑",
            description="你是怎么拿到这东西的（警觉）",
            rarity=Rarity.COMMON,
            physical_bonus=10,
            magical_bonus=5
        ),
        
        "iron_sword": Weapon(
            name="铁剑",
            description="标准的铁制长剑",
            rarity=Rarity.UNCOMMON,
            physical_bonus=20,
            magical_bonus=5
        ),
        
        "magic_staff": Weapon(
            name="魔法杖",
            description="蕴含魔力的法杖",
            rarity=Rarity.RARE,
            physical_bonus=5,
            magical_bonus=25
        ),
    }
    
    return weapons


# ==================== 防具数据库 ====================

def create_armor_database():
    """创建防具数据库"""
    armors = {
        "none": Armor(
            name="",
            description="",
            rarity=Rarity.COMMON,
            block_value=0
        ),
        
        "cloth": Armor(
            name="布衣",
            description="普通的布制衣服",
            rarity=Rarity.COMMON,
            block_value=15
        ),
        
        "leather": Armor(
            name="皮甲",
            description="轻便的皮革护甲",
            rarity=Rarity.UNCOMMON,
            block_value=25
        ),
        
        "plate": Armor(
            name="板甲",
            description="厚重的金属板甲",
            rarity=Rarity.RARE,
            block_value=40
        ),
    }
    
    return armors


# ==================== 预设角色 ====================

def create_player_character():
    """创建玩家角色"""
    from models import Entity
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # 构建卡组
    deck = [
        cards_db["basic_attack"].copy(),
        cards_db["basic_attack"].copy(),
        cards_db["basic_attack"].copy(),
        cards_db["basic_attack"].copy(),
        cards_db["serious_strike"].copy(),
        cards_db["block"].copy(),
        cards_db["block"].copy(),
        cards_db["poison"].copy(),
        cards_db["poison"].copy(),
        cards_db["poison"].copy(),
    ]
    
    # 装备
    equipment = {
        "weapon": weapons_db["wooden_sword"],
        "armor": armors_db["cloth"]
    }
    
    # 属性
    stats = Stats(
        strength=14,
        dexterity=14,
        constitution=10,
        intelligence=8,
        wisdom=14,
        charisma=8
    )
    
    player = Entity(
        name="mimi",
        max_hp=200,
        max_ap=3,
        equipment=equipment,
        cards=deck,
        hand_size=4,
        stats=stats,
        control_type=ControlType.PLAYER,
        position=(2, 7)
    )
    
    return player


def create_enemy():
    """创建敌人"""
    from models import Entity
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # 敌人卡组
    deck = [
        cards_db["basic_attack"].copy(),
        cards_db["basic_attack"].copy(),
        cards_db["basic_attack"].copy(),
        cards_db["basic_attack"].copy(),
    ]
    
    # 装备
    equipment = {
        "weapon": weapons_db["wooden_sword"],
        "armor": armors_db["cloth"]
    }
    
    enemy = Entity(
        name="meowcake",
        max_hp=200,
        max_ap=3,
        equipment=equipment,
        cards=deck,
        hand_size=4,
        control_type=ControlType.AI,
        position=(17, 7)
    )
    
    return enemy


def create_ally_ai():
    """创建AI控制的队友"""
    from models import Entity
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # AI队友卡组
    deck = [
        cards_db["basic_attack"].copy(),
        cards_db["basic_attack"].copy(),
        cards_db["block"].copy(),
        cards_db["heal"].copy(),
    ]
    
    # 装备
    equipment = {
        "weapon": weapons_db["iron_sword"],
        "armor": armors_db["leather"]
    }
    
    ally = Entity(
        name="AI队友",
        max_hp=180,
        max_ap=3,
        equipment=equipment,
        cards=deck,
        hand_size=4,
        control_type=ControlType.AI,
        position=(4, 7)
    )
    
    return ally


def create_enemy_2():
    """创建第二个敌人"""
    from models import Entity
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # 敌人卡组
    deck = [
        cards_db["fireball"].copy(),
        cards_db["fireball"].copy(),
        cards_db["shield"].copy(),
        cards_db["basic_attack"].copy(),
    ]
    
    # 装备
    equipment = {
        "weapon": weapons_db["magic_staff"],
        "armor": armors_db["plate"]
    }
    
    enemy = Entity(
        name="魔法敌人",
        max_hp=150,
        max_ap=4,
        equipment=equipment,
        cards=deck,
        hand_size=4,
        control_type=ControlType.AI,
        position=(15, 5)
    )
    
    return enemy

"""
卡牌数据库模块
定义所有可用的卡牌、武器和防具
"""
import os
from models import Card, Weapon, Armor, Stats, ControlType
from config import Rarity, CardType, TargetType, CONSTANTS
from card_serializer import CardSerializer


# ==================== 卡牌数据库 ====================

def create_card_database():
    """创建卡牌数据库 - 从JSON文件读取"""
    # 尝试从JSON文件加载卡牌
    json_file = os.path.join(os.path.dirname(__file__), 'cards.json')
    
    if os.path.exists(json_file):
        try:
            cards_list = CardSerializer.load_cards_from_file(json_file)
            # 转换为字典格式，以卡牌名称为键
            cards = {card.name: card for card in cards_list}
            return cards
        except Exception as e:
            print(f"警告：从JSON文件加载卡牌失败: {e}")
            print("使用默认卡牌...")
    
    # 如果JSON文件不存在或加载失败，返回空字典
    return {}


# ==================== 武器数据库 ====================

def create_weapon_database():
    """创建武器数据库 - 从JSON文件读取"""
    from card_serializer import CardSerializer
    
    # 尝试从JSON文件加载装备
    json_file = os.path.join(os.path.dirname(__file__), 'equipments.json')
    
    weapons = {}
    
    if os.path.exists(json_file):
        try:
            all_equipments = CardSerializer.load_equipments_from_file(json_file)
            # 筛选出武器
            for eq in all_equipments:
                if hasattr(eq, 'physical_bonus'):
                    # 使用英文名作为键（兼容性）
                    key = eq.name.lower().replace(" ", "_")
                    # 特殊映射
                    name_to_key = {
                        "训练木剑": "wooden_sword",
                        "铁剑": "iron_sword",
                        "魔法杖": "magic_staff",
                        "手半剑": "bastard_sword"
                    }
                    if eq.name in name_to_key:
                        key = name_to_key[eq.name]
                    weapons[key] = eq
            
            # 添加一个空武器作为默认值
            if "none" not in weapons:
                from models import Weapon
                weapons["none"] = Weapon(
                    name="",
                    description="",
                    rarity=Rarity.COMMON,
                    physical_bonus=0,
                    magical_bonus=0,
                    attack_modifier=0
                )
            
            return weapons
        except Exception as e:
            print(f"警告：从JSON文件加载武器失败: {e}")
            print("使用默认武器...")
    
    # 如果JSON文件不存在或加载失败，返回默认武器
    from models import Weapon
    default_weapons = {
        "none": Weapon(
            name="",
            description="",
            rarity=Rarity.COMMON,
            physical_bonus=0,
            magical_bonus=0,
            attack_modifier=0
        ),
        
        "wooden_sword": Weapon(
            name="训练木剑",
            description="你是怎么拿到这东西的（警觉）",
            rarity=Rarity.COMMON,
            physical_bonus=10,
            magical_bonus=5,
            attack_modifier=0
        ),
        
        "iron_sword": Weapon(
            name="铁剑",
            description="标准的铁制长剑",
            rarity=Rarity.UNCOMMON,
            physical_bonus=20,
            magical_bonus=5,
            attack_modifier=1
        ),
        
        "magic_staff": Weapon(
            name="魔法杖",
            description="蕴含魔力的法杖",
            rarity=Rarity.RARE,
            physical_bonus=5,
            magical_bonus=25,
            attack_modifier=2
        ),
        
        "bastard_sword": Weapon(
            name="手半剑",
            description="灵活的双刃剑，提供刺击和劈砍选项",
            rarity=Rarity.UNCOMMON,
            physical_bonus=15,
            magical_bonus=0,
            attack_modifier=2,
            provided_cards=["刺击", "劈砍"]
        ),
    }
    
    # 合并JSON加载的武器和默认武器（JSON优先）
    default_weapons.update(weapons)
    return default_weapons


# ==================== 防具数据库 ====================

def create_armor_database():
    """创建防具数据库 - 从JSON文件读取"""
    from card_serializer import CardSerializer
    
    # 尝试从JSON文件加载装备
    json_file = os.path.join(os.path.dirname(__file__), 'equipments.json')
    
    armors = {}
    
    if os.path.exists(json_file):
        try:
            all_equipments = CardSerializer.load_equipments_from_file(json_file)
            # 筛选出防具
            for eq in all_equipments:
                if hasattr(eq, 'block_dice') or hasattr(eq, 'block_value'):
                    # 使用英文名作为键（兼容性）
                    key = eq.name.lower().replace(" ", "_")
                    # 特殊映射
                    name_to_key = {
                        "布衣": "cloth",
                        "皮甲": "leather",
                        "板甲": "plate",
                        "圆盾": "round_shield",
                        "轻型护甲": "light_armor",
                        "中型护甲": "medium_armor",
                        "重型护甲": "heavy_armor"
                    }
                    if eq.name in name_to_key:
                        key = name_to_key[eq.name]
                    armors[key] = eq
            
            # 添加一个空防具作为默认值
            if "none" not in armors:
                from models import Armor
                armors["none"] = Armor(
                    name="",
                    description="",
                    rarity=Rarity.COMMON,
                    block_value=0,
                    block_dice="",
                    block_per_turn=0,
                    ap_bonus=0
                )
            
            return armors
        except Exception as e:
            print(f"警告：从JSON文件加载防具失败: {e}")
            print("使用默认防具...")
    
    # 如果JSON文件不存在或加载失败，返回默认防具
    from models import Armor
    default_armors = {
        "none": Armor(
            name="",
            description="",
            rarity=Rarity.COMMON,
            block_value=0,
            block_dice="",
            block_per_turn=0,
            ap_bonus=0
        ),
        
        "cloth": Armor(
            name="布衣",
            description="普通的布制衣服",
            rarity=Rarity.COMMON,
            block_value=0,
            block_dice="2d2",
            block_per_turn=0,
            ap_bonus=0
        ),
        
        "leather": Armor(
            name="皮甲",
            description="轻便的皮革护甲",
            rarity=Rarity.UNCOMMON,
            block_value=0,
            block_dice="2d3",
            block_per_turn=0,
            ap_bonus=0
        ),
        
        "plate": Armor(
            name="板甲",
            description="厚重的金属板甲",
            rarity=Rarity.RARE,
            block_value=0,
            block_dice="2d4",
            block_per_turn=0,
            ap_bonus=0
        ),
        
        "round_shield": Armor(
            name="圆盾",
            description="提供每回合再生格挡值和消耗AP的格挡牌",
            rarity=Rarity.UNCOMMON,
            block_value=0,
            block_dice="2d2",
            block_per_turn=5,
            ap_bonus=0,
            provided_cards=["盾牌格挡"]
        ),
        
        "light_armor": Armor(
            name="轻型护甲",
            description="根据敏捷和力量提升AP",
            rarity=Rarity.COMMON,
            block_value=0,
            block_dice="2d2",
            block_per_turn=0,
            ap_bonus=0
        ),
        
        "medium_armor": Armor(
            name="中型护甲",
            description="平衡的防护，提供额外AP",
            rarity=Rarity.UNCOMMON,
            block_value=0,
            block_dice="2d3",
            block_per_turn=0,
            ap_bonus=0
        ),
        
        "heavy_armor": Armor(
            name="重型护甲",
            description="最强防护，显著提升AP",
            rarity=Rarity.RARE,
            block_value=0,
            block_dice="2d4",
            block_per_turn=0,
            ap_bonus=0
        ),
    }
    
    # 合并JSON加载的防具和默认防具（JSON优先）
    default_armors.update(armors)
    return default_armors


# ==================== 预设角色 ====================

def create_player_character():
    """创建玩家角色"""
    from models import Entity
    from inventory import Inventory, InventoryItem, ItemShape, ItemType
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # 构建卡组（从 JSON 加载的卡牌）
    deck = []
    
    # 如果 JSON 中有这些卡牌，则使用它们
    if "刺击" in cards_db:
        deck.extend([cards_db["刺击"].copy() for _ in range(4)])
    if "劈砍" in cards_db:
        deck.append(cards_db["劈砍"].copy())
    if "格挡" in cards_db:
        deck.extend([cards_db["格挡"].copy() for _ in range(2)])
    if "投毒" in cards_db:
        deck.extend([cards_db["投毒"].copy() for _ in range(3)])
    
    # 如果卡组为空，添加默认卡牌
    if not deck:
        # 创建一些默认卡牌作为后备
        from models import Card
        from config import CardType, Rarity
        deck = [
            Card("普攻", CardType.ATTACK_PHYSICAL, 1, {"hp": -10}, "基础攻击", Rarity.COMMON),
            Card("普攻", CardType.ATTACK_PHYSICAL, 1, {"hp": -10}, "基础攻击", Rarity.COMMON),
            Card("普攻", CardType.ATTACK_PHYSICAL, 1, {"hp": -10}, "基础攻击", Rarity.COMMON),
            Card("普攻", CardType.ATTACK_PHYSICAL, 1, {"hp": -10}, "基础攻击", Rarity.COMMON),
        ]
    
    # 常驻卡牌（不参与抽牌，每回合自动在手牌中）
    permanent_cards = []
    if "基础移动" in cards_db:
        permanent_cards.append(cards_db["基础移动"].copy())
    
    # 装备（使用EquipmentManager管理）
    equipment = {
        "weapon": weapons_db.get("wooden_sword"),
        "armor": armors_db.get("cloth")
    }
    
    # 属性
    stats = Stats(
        strength=14,
        dexterity=14,
        intelligence=8,
        charisma=8
    )
    
    # 创建背包并添加初始物品
    inventory = Inventory(
        owner_name="mimi",
        grid_width=CONSTANTS.INVENTORY_WIDTH,
        grid_height=CONSTANTS.INVENTORY_HEIGHT,
        max_volume=CONSTANTS.INVENTORY_MAX_VOLUME,
        max_weight=CONSTANTS.INVENTORY_MAX_WEIGHT
    )
    
    # 添加一些初始物品
    initial_items = [
        InventoryItem(
            name="生命药水",
            item_type=ItemType.CONSUMABLE,
            description="恢复生命值的药水",
            weight=0.5,
            volume=1,
            shape=ItemShape.SINGLE,
            icon_color=(255, 100, 100),
            stackable=True,
            max_stack=10,
            stack_count=3,
            use_effects={"heal": 50},  # 恢复50点生命值
            ap_cost=1  # 消耗1点AP
        ),
        InventoryItem(
            name="AP药水",
            item_type=ItemType.CONSUMABLE,
            description="恢复行动点的药水",
            weight=0.3,
            volume=1,
            shape=ItemShape.SINGLE,
            icon_color=(100, 100, 255),
            stackable=True,
            max_stack=5,
            stack_count=2,
            use_effects={"restore_ap": 2},  # 恢复2点AP
            ap_cost=1  # 使用不消耗AP
        ),
        InventoryItem(
            name="铁剑",
            item_type=ItemType.WEAPON,
            description="一把备用的铁剑",
            weight=3.0,
            volume=2,
            shape=ItemShape.VERTICAL_2,
            icon_color=(200, 200, 200)
        ),
        InventoryItem(
            name="木盾",
            item_type=ItemType.ARMOR,
            description="简易的木制盾牌",
            weight=2.5,
            volume=2,
            shape=ItemShape.SQUARE_2X2,
            icon_color=(139, 69, 19)
        ),
    ]
    
    for item in initial_items:
        inventory.add_item(item)
    
    player = Entity(
        name="mimi",
        max_hp=10,  # 初始血量为10
        max_ap=3,
        equipment=equipment,
        cards=deck,
        hand_size=4,
        stats=stats,
        control_type=ControlType.PLAYER,
        position=(2, 7),
        permanent_cards=permanent_cards,  # 传入常驻卡牌
        inventory=inventory  # 传入背包
    )
    
    return player


def create_enemy():
    """创建敌人"""
    from models import Entity
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # 敌人卡组 - 至少10张
    deck = []
    if "刺击" in cards_db:
        deck.extend([cards_db["刺击"].copy() for _ in range(5)])
    if "劈砍" in cards_db:
        deck.extend([cards_db["劈砍"].copy() for _ in range(3)])
    if "格挡" in cards_db:
        deck.extend([cards_db["格挡"].copy() for _ in range(2)])
    
    # 如果卡组不足10张，补充默认卡牌
    while len(deck) < 10:
        deck.append(Card("普攻", CardType.ATTACK_PHYSICAL, 1, {"hp": -10}, "基础攻击", Rarity.COMMON))
    
    # 装备（使用EquipmentManager管理）
    equipment = {
        "weapon": weapons_db.get("wooden_sword"),
        "armor": armors_db.get("cloth")
    }
    
    enemy = Entity(
        name="meowcake",
        max_hp=10,  # 初始血量为10
        max_ap=3,
        equipment=equipment,
        cards=deck,
        hand_size=7,  # 手牌上限7张（不含常驻牌）
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
    
    # AI队友卡组 - 至少10张
    deck = []
    if "刺击" in cards_db:
        deck.extend([cards_db["刺击"].copy() for _ in range(4)])
    if "劈砍" in cards_db:
        deck.extend([cards_db["劈砍"].copy() for _ in range(2)])
    if "格挡" in cards_db:
        deck.extend([cards_db["格挡"].copy() for _ in range(2)])
    if "治疗" in cards_db:
        deck.extend([cards_db["治疗"].copy() for _ in range(2)])
    
    # 如果卡组不足10张，补充默认卡牌
    while len(deck) < 10:
        deck.append(Card("普攻", CardType.ATTACK_PHYSICAL, 1, {"hp": -10}, "基础攻击", Rarity.COMMON))
    
    # 装备（使用EquipmentManager管理）
    equipment = {
        "weapon": weapons_db.get("iron_sword"),
        "armor": armors_db.get("leather")
    }
    
    ally = Entity(
        name="AI队友",
        max_hp=10,  # 初始血量为10
        max_ap=3,
        equipment=equipment,
        cards=deck,
        hand_size=7,  # 手牌上限7张（不含常驻牌）
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
    
    # 敌人卡组 - 至少10张
    deck = []
    if "劈砍" in cards_db:
        deck.extend([cards_db["劈砍"].copy() for _ in range(3)])
    if "刺击" in cards_db:
        deck.extend([cards_db["刺击"].copy() for _ in range(3)])
    if "格挡" in cards_db:
        deck.extend([cards_db["格挡"].copy() for _ in range(2)])
    if "治疗" in cards_db:
        deck.extend([cards_db["治疗"].copy() for _ in range(2)])
    
    # 如果卡组不足10张，补充默认卡牌
    while len(deck) < 10:
        deck.append(Card("火球术", CardType.ATTACK_MAGICAL, 2, {"hp": -20}, "魔法攻击", Rarity.UNCOMMON))
    
    # 装备（使用EquipmentManager管理）
    equipment = {
        "weapon": weapons_db.get("magic_staff"),
        "armor": armors_db.get("plate")
    }
    
    enemy = Entity(
        name="魔法敌人",
        max_hp=10,  # 初始血量为10
        max_ap=4,
        equipment=equipment,
        cards=deck,
        hand_size=7,  # 手牌上限7张（不含常驻牌）
        control_type=ControlType.AI,
        position=(15, 5)
    )
    
    return enemy

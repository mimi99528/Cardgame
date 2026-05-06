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
    cards = {}
    
    # 1. 尝试从主JSON文件加载卡牌
    json_file = os.path.join(os.path.dirname(__file__), 'cards.json')
    
    if os.path.exists(json_file):
        try:
            cards_list = CardSerializer.load_cards_from_file(json_file)
            # 转换为字典格式，以卡牌名称为键
            cards.update({card.name: card for card in cards_list})
        except Exception as e:
            print(f"警告：从JSON文件加载卡牌失败: {e}")
    
    # 2. 从./cards文件夹加载单独的卡牌文件
    cards_dir = os.path.join(os.path.dirname(__file__), 'cards')
    if os.path.exists(cards_dir):
        try:
            for filename in os.listdir(cards_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(cards_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            import json
                            card_data = json.load(f)
                            
                            # 支持列表格式（多个卡牌）或单个卡牌对象
                            if isinstance(card_data, list):
                                # 列表格式：遍历所有卡牌
                                for data in card_data:
                                    card = CardSerializer.dict_to_card(data)
                                    cards[card.name] = card
                            else:
                                # 单个卡牌对象
                                card = CardSerializer.dict_to_card(card_data)
                                cards[card.name] = card
                    except Exception as e:
                        print(f"警告：加载卡牌文件 {filename} 失败: {e}")
        except Exception as e:
            print(f"警告：扫描cards目录失败: {e}")
    
    return cards


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
                        "重型护甲": "heavy_armor",
                        "学徒法袍": "apprentice_robe"
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


# ==================== 饰品数据库 ====================

def create_accessory_database():
    """创建饰品数据库 - 从JSON文件读取"""
    from card_serializer import CardSerializer
    from models import Accessory
    
    # 尝试从JSON文件加载装备
    json_file = os.path.join(os.path.dirname(__file__), 'equipments.json')
    
    accessories = {}
    
    if os.path.exists(json_file):
        try:
            all_equipments = CardSerializer.load_equipments_from_file(json_file)
            # 筛选出饰品（通过类型检查）
            for eq in all_equipments:
                if isinstance(eq, Accessory):
                    # 使用英文名作为键
                    key = eq.name.lower().replace(" ", "_")
                    accessories[key] = eq
            
            return accessories
        except Exception as e:
            print(f"警告：从JSON文件加载饰品失败: {e}")
            import traceback
            traceback.print_exc()
            print("使用默认饰品...")
    
    # 如果JSON文件不存在或加载失败，返回空字典
    return accessories


# ==================== 职业专属卡组 ====================

def create_drifter_deck():
    """创建流浪者专属卡组 - 敏捷型、生存导向"""
    cards_db = create_card_database()
    deck = []
    
    # 核心攻击卡
    if "精准打击" in cards_db:
        deck.extend([cards_db["精准打击"].copy() for _ in range(3)])
    if "刺击" in cards_db:
        deck.append(cards_db["刺击"].copy())
    
    # 移动和生存卡
    if "疾风步" in cards_db:
        deck.extend([cards_db["疾风步"].copy() for _ in range(2)])
    if "野外求生" in cards_db:
        deck.append(cards_db["野外求生"].copy())
    
    # 防御卡
    if "灵巧闪避" in cards_db:
        deck.extend([cards_db["灵巧闪避"].copy() for _ in range(2)])
    if "格挡" in cards_db:
        deck.append(cards_db["格挡"].copy())
    
    # 补充到10张（不包括基础移动，因为它是常驻牌）
    while len(deck) < 10:
        if "基础移动" in cards_db:
            # 基础移动是常驻牌，不应该加入卡组
            break
        else:
            break
    
    return deck


def create_artisan_deck():
    """创建手艺人专属卡组 - 力量型、装备导向"""
    cards_db = create_card_database()
    deck = []
    
    # 核心攻击卡
    if "重击" in cards_db:
        deck.extend([cards_db["重击"].copy() for _ in range(2)])
    if "劈砍" in cards_db:
        deck.extend([cards_db["劈砍"].copy() for _ in range(2)])
    
    # 装备交互卡
    if "工具修理" in cards_db:
        deck.extend([cards_db["工具修理"].copy() for _ in range(2)])
    
    # 防御卡
    if "坚固防御" in cards_db:
        deck.extend([cards_db["坚固防御"].copy() for _ in range(2)])
    if "格挡" in cards_db:
        deck.append(cards_db["格挡"].copy())
    
    # 补充到10张
    while len(deck) < 10:
        if "刺击" in cards_db:
            deck.append(cards_db["刺击"].copy())
        else:
            break
    
    return deck


def create_pedlar_deck():
    """创建行商专属卡组 - 魅力型、控制导向"""
    cards_db = create_card_database()
    deck = []
    
    # 核心攻击卡
    if "洞察弱点" in cards_db:
        deck.extend([cards_db["洞察弱点"].copy() for _ in range(3)])
    
    # 社交和控制卡
    if "巧言令色" in cards_db:
        deck.extend([cards_db["巧言令色"].copy() for _ in range(2)])
    if "贿赂" in cards_db:
        deck.append(cards_db["贿赂"].copy())
    
    # 防御卡
    if "格挡" in cards_db:
        deck.extend([cards_db["格挡"].copy() for _ in range(2)])
    
    # 补充到10张
    while len(deck) < 10:
        if "刺击" in cards_db:
            deck.append(cards_db["刺击"].copy())
        else:
            break
    
    return deck


def create_farmer_deck():
    """创建农民专属卡组 - 力量/心智型、坦克导向"""
    cards_db = create_card_database()
    deck = []
    
    # 核心攻击卡
    if "丰收之击" in cards_db:
        deck.extend([cards_db["丰收之击"].copy() for _ in range(2)])
    if "劈砍" in cards_db:
        deck.append(cards_db["劈砍"].copy())
    
    # 治疗和群体卡
    if "坚韧不拔" in cards_db:
        deck.extend([cards_db["坚韧不拔"].copy() for _ in range(2)])
    if "群体鼓舞" in cards_db:
        deck.append(cards_db["群体鼓舞"].copy())
    
    # 防御卡
    if "大地守护" in cards_db:
        deck.extend([cards_db["大地守护"].copy() for _ in range(2)])
    
    # 补充到10张
    while len(deck) < 10:
        if "格挡" in cards_db:
            deck.append(cards_db["格挡"].copy())
        else:
            break
    
    return deck


def create_scholar_deck():
    """创建学者专属卡组 - 心智型、法术导向"""
    cards_db = create_card_database()
    deck = []
    
    # 核心法术卡
    if "奥术冲击" in cards_db:
        deck.extend([cards_db["奥术冲击"].copy() for _ in range(3)])
    if "心灵震爆" in cards_db:
        deck.append(cards_db["心灵震爆"].copy())
    
    # 资源管理卡
    if "知识汲取" in cards_db:
        deck.extend([cards_db["知识汲取"].copy() for _ in range(2)])
    if "思维加速" in cards_db:
        deck.append(cards_db["思维加速"].copy())
    
    # 防御卡
    if "法力护盾" in cards_db:
        deck.extend([cards_db["法力护盾"].copy() for _ in range(2)])
    
    # 补充到10张
    while len(deck) < 10:
        if "冰缀" in cards_db:
            deck.append(cards_db["冰缀"].copy())
        else:
            break
    
    return deck


def get_career_deck(career_type):
    """根据职业类型获取专属卡组"""
    from career_system import CareerType
    
    deck_functions = {
        CareerType.DRIFTER: create_drifter_deck,
        CareerType.ARTISAN: create_artisan_deck,
        CareerType.PEDLAR: create_pedlar_deck,
        CareerType.FARMER: create_farmer_deck,
        CareerType.SCHOLAR: create_scholar_deck,
    }
    
    func = deck_functions.get(career_type)
    if func:
        return func()
    else:
        # 默认卡组
        return create_drifter_deck()


# ==================== 敌人职业卡组 ====================

def create_enemy_warrior_deck():
    """创建战士型敌人卡组 - 高攻击、中等防御"""
    cards_db = create_card_database()
    deck = []
    
    if "劈砍" in cards_db:
        deck.extend([cards_db["劈砍"].copy() for _ in range(4)])
    if "刺击" in cards_db:
        deck.extend([cards_db["刺击"].copy() for _ in range(3)])
    if "破绽打击" in cards_db:
        deck.append(cards_db["破绽打击"].copy())
    if "格挡" in cards_db:
        deck.extend([cards_db["格挡"].copy() for _ in range(2)])
    
    while len(deck) < 10:
        if "刺击" in cards_db:
            deck.append(cards_db["刺击"].copy())
        else:
            break
    
    return deck


def create_enemy_mage_deck():
    """创建法师型敌人卡组 - 高伤害法术、低防御"""
    cards_db = create_card_database()
    deck = []
    
    if "奥术飞弹" in cards_db:
        deck.extend([cards_db["奥术飞弹"].copy() for _ in range(2)])
    if "点火" in cards_db:
        deck.extend([cards_db["点火"].copy() for _ in range(2)])
    if "冰缀" in cards_db:
        deck.extend([cards_db["冰缀"].copy() for _ in range(2)])
    if "法力护盾" in cards_db:
        deck.extend([cards_db["法力护盾"].copy() for _ in range(2)])
    if "奥术冲击" in cards_db:
        deck.append(cards_db["奥术冲击"].copy())
    
    while len(deck) < 10:
        if "冰缀" in cards_db:
            deck.append(cards_db["冰缀"].copy())
        else:
            break
    
    return deck


def create_enemy_tank_deck():
    """创建坦克型敌人卡组 - 高防御、持续作战"""
    cards_db = create_card_database()
    deck = []
    
    if "格挡" in cards_db:
        deck.extend([cards_db["格挡"].copy() for _ in range(4)])
    if "盾牌格挡" in cards_db:
        deck.extend([cards_db["盾牌格挡"].copy() for _ in range(2)])
    if "刺击" in cards_db:
        deck.extend([cards_db["刺击"].copy() for _ in range(3)])
    if "治疗" in cards_db:
        deck.append(cards_db["治疗"].copy())
    
    while len(deck) < 10:
        if "格挡" in cards_db:
            deck.append(cards_db["格挡"].copy())
        else:
            break
    
    return deck


def create_enemy_assassin_deck():
    """创建刺客型敌人卡组 - 高爆发、毒药"""
    cards_db = create_card_database()
    deck = []
    
    if "投毒" in cards_db:
        deck.extend([cards_db["投毒"].copy() for _ in range(3)])
    if "刺击" in cards_db:
        deck.extend([cards_db["刺击"].copy() for _ in range(3)])
    if "破绽打击" in cards_db:
        deck.extend([cards_db["破绽打击"].copy() for _ in range(2)])
    if "精准打击" in cards_db:
        deck.append(cards_db["精准打击"].copy())
    
    while len(deck) < 10:
        if "刺击" in cards_db:
            deck.append(cards_db["刺击"].copy())
        else:
            break
    
    return deck


def get_enemy_deck(enemy_type="warrior"):
    """根据敌人类型获取卡组"""
    deck_functions = {
        "warrior": create_enemy_warrior_deck,
        "mage": create_enemy_mage_deck,
        "tank": create_enemy_tank_deck,
        "assassin": create_enemy_assassin_deck,
    }
    
    func = deck_functions.get(enemy_type, create_enemy_warrior_deck)
    return func()


# ==================== 预设角色 ====================

def create_player_character(career_type=None):
    """
    创建玩家角色
    
    Args:
        career_type: 职业类型（可选），如果不指定则使用默认卡组
    """
    from models import Entity
    from inventory import Inventory, InventoryItem, ItemShape, ItemType
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # 根据职业获取专属卡组
    if career_type:
        deck = get_career_deck(career_type)
    else:
        # 默认卡组（向后兼容）
        deck = []
        if "刺击" in cards_db:
            deck.extend([cards_db["刺击"].copy() for _ in range(4)])
        if "劈砍" in cards_db:
            deck.append(cards_db["劈砍"].copy())
        if "格挡" in cards_db:
            deck.extend([cards_db["格挡"].copy() for _ in range(2)])
        if "投毒" in cards_db:
            deck.extend([cards_db["投毒"].copy() for _ in range(3)])
        
        # 添加法术卡牌（测试用）
        if "冰缀" in cards_db:
            deck.append(cards_db["冰缀"].copy())
        if "点火" in cards_db:
            deck.append(cards_db["点火"].copy())
        if "治疗之光" in cards_db:
            deck.append(cards_db["治疗之光"].copy())
    
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


def create_enemy(enemy_type="warrior"):
    """
    创建敌人
    
    Args:
        enemy_type: 敌人类型 (warrior/mage/tank/assassin)
    """
    from models import Entity
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # 根据敌人类型获取专属卡组
    deck = get_enemy_deck(enemy_type)
    
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


def create_ally_ai(career_type=None):
    """
    创建AI控制的队友
    
    Args:
        career_type: 职业类型（可选）
    """
    from models import Entity
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # AI队友卡组 - 根据职业或默认
    if career_type:
        deck = get_career_deck(career_type)
    else:
        # 默认均衡卡组
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


def create_enemy_2(enemy_type="mage"):
    """
    创建第二个敌人
    
    Args:
        enemy_type: 敌人类型 (warrior/mage/tank/assassin)
    """
    from models import Entity
    
    cards_db = create_card_database()
    weapons_db = create_weapon_database()
    armors_db = create_armor_database()
    
    # 敌人卡组 - 根据类型
    deck = get_enemy_deck(enemy_type)
    
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

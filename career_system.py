"""
职业系统模块
包含职业基类、职业管理器以及职业序列化功能
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import os


class CareerType(Enum):
    """职业类型枚举"""
    DRIFTER = "drifter"           # 流浪者
    ARTISAN = "artisan"           # 手艺人
    PEDLAR = "pedlar"            # 行商/说书人
    FARMER = "farmer"            # 农民
    SCHOLAR = "scholar"          # 游学青年


@dataclass
class CareerPassive:
    """职业被动效果"""
    name: str                    # 被动名称
    description: str             # 被动描述
    career_type: CareerType      # 所属职业
    effect_handler: Optional[str] = None  # 效果处理器函数名（用于事件订阅）
    required_cards: List[str] = field(default_factory=list)  # 需要的特殊卡牌名称列表
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "career_type": self.career_type.value,
            "effect_handler": self.effect_handler,
            "required_cards": self.required_cards
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CareerPassive':
        """从字典反序列化"""
        return CareerPassive(
            name=data["name"],
            description=data["description"],
            career_type=CareerType(data["career_type"]),
            effect_handler=data.get("effect_handler"),
            required_cards=data.get("required_cards", [])
        )


class Career:
    """职业基类"""
    
    def __init__(self, career_type: CareerType, name: str, description: str, hit_dice_type: int = 8):
        self.career_type = career_type
        self.name = name
        self.description = description
        self.passives: List[CareerPassive] = []
        self.special_cards: List[str] = []  # 职业特殊卡牌名称列表
        self.initial_deck_config: Dict[str, Any] = {}  # 初始卡组配置
        self.hit_dice_type = hit_dice_type  # 生命骰类型（d4, d6, d8, d10, d12等）
        
    def add_passive(self, passive: CareerPassive):
        """添加被动效果"""
        self.passives.append(passive)
        
    def set_initial_deck(self, deck_config: Dict[str, Any]):
        """
        设置初始卡组配置
        
        Args:
            deck_config: 卡组配置字典，格式为 {"card_name": count}
        """
        self.initial_deck_config = deck_config
        
    def get_all_required_cards(self) -> List[str]:
        """获取所有需要的特殊卡牌"""
        cards = set()
        for passive in self.passives:
            cards.update(passive.required_cards)
        cards.update(self.special_cards)
        return list(cards)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "career_type": self.career_type.value,
            "name": self.name,
            "description": self.description,
            "passives": [p.to_dict() for p in self.passives],
            "special_cards": self.special_cards,
            "initial_deck_config": self.initial_deck_config,
            "hit_dice_type": self.hit_dice_type
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Career':
        """从字典反序列化"""
        career = Career(
            career_type=CareerType(data["career_type"]),
            name=data["name"],
            description=data["description"],
            hit_dice_type=data.get("hit_dice_type", 8)
        )
        career.passives = [CareerPassive.from_dict(p) for p in data.get("passives", [])]
        career.special_cards = data.get("special_cards", [])
        career.initial_deck_config = data.get("initial_deck_config", {})
        return career
    
    def __str__(self):
        return f"{self.name} ({self.career_type.value})"


# ==================== 具体职业实现 ====================

def create_drifter_career() -> Career:
    """创建流浪者职业"""
    career = Career(
        career_type=CareerType.DRIFTER,
        name="流浪者",
        description="轻装简从的旅行者，擅长生存和探索",
        hit_dice_type=8  # d8生命骰
    )
    
    # 被动1：轻装简从
    passive1 = CareerPassive(
        name="轻装简从",
        description="手牌中[移动/探索]标签卡不计入手牌软上限（最多2张）；大地图节点间食物消耗-1fu(food unit)",
        career_type=CareerType.DRIFTER,
        effect_handler="drifter_light_pack_handler",
        required_cards=["应急包扎"]
    )
    career.add_passive(passive1)
    
    # 特殊卡牌
    career.special_cards = ["应急包扎"]
    
    # 初始卡组配置（1~6号卡分别有3、3、2、2、1、1张，共12张；7~8号Legendary卡不在初始卡组）
    career.set_initial_deck({
        "疾风步": 3,           # 101 - Common
        "野外求生": 3,         # 102 - Common
        "灵巧闪避": 2,         # 103 - Common
        "精准打击": 2,         # 104 - Uncommon
        "影遁": 1,             # 105 - Uncommon
        "荒野直觉": 1          # 106 - Rare
        # 107 风行斩 (Rare) - 不在初始卡组
        # 108 流浪者之魂 (Legendary) - 不在初始卡组
    })
    
    return career


def create_artisan_career() -> Career:
    """创建手艺人职业"""
    career = Career(
        career_type=CareerType.ARTISAN,
        name="手艺人",
        description="精通装备使用的工匠，善于资源管理",
        hit_dice_type=8  # d8生命骰
    )
    
    # 被动1：物尽其用
    passive1 = CareerPassive(
        name="物尽其用",
        description="装备赋予的卡牌效果+1（伤害/回复）；在安全节点可消耗1份[材料]标签的物品，将1张手牌临时添加[工具]标签（持续1次遭遇）",
        career_type=CareerType.ARTISAN,
        effect_handler="artisan_make_best_use_handler",
        required_cards=["临时加固"]
    )
    career.add_passive(passive1)
    
    # 特殊卡牌
    career.special_cards = ["临时加固"]
    
    # 初始卡组配置（1~6号卡分别有3、3、2、2、1、1张，共12张；7~8号Legendary卡不在初始卡组）
    career.set_initial_deck({
        "坚固防御": 3,         # 201 - Common
        "重击": 3,             # 202 - Common
        "工具修理": 2,         # 203 - Common
        "战地修缮": 2,         # 204 - Uncommon
        "临时锻造": 1,         # 205 - Uncommon
        "谨慎防御": 1          # 206 - Rare
        # 207 符文刻印 (Rare) - 不在初始卡组
        # 208 大师之作 (Legendary) - 不在初始卡组
    })
    
    return career


def create_pedlar_career() -> Career:
    """创建行商/说书人职业"""
    career = Career(
        career_type=CareerType.PEDLAR,
        name="行商/说书人",
        description="见多识广的商人，擅长社交和情报收集",
        hit_dice_type=6  # d6生命骰
    )
    
    # 被动1：见多识广
    passive1 = CareerPassive(
        name="见多识广",
        description="魅力相关检定结果距(Margin)+1；非主线剧情类社交检定失败时可消耗1点幸运重掷（每场遭遇限1次）",
        career_type=CareerType.PEDLAR,
        effect_handler="pedlar_well_traveled_handler",
        required_cards=["讨价还价"]
    )
    career.add_passive(passive1)
    
    # 特殊卡牌
    career.special_cards = ["讨价还价"]
    
    # 初始卡组配置（1~6号卡分别有3、3、2、2、1、1张，共12张；7~8号Legendary卡不在初始卡组）
    career.set_initial_deck({
        "巧言令色": 3,         # 301 - Common
        "洞察弱点": 3,         # 302 - Common
        "贿赂": 2,             # 303 - Common
        "外交斡旋": 2,         # 304 - Uncommon
        "商人直觉": 1,         # 305 - Uncommon
        "传奇故事": 1          # 306 - Rare
        # 307 孤注一掷 (Rare) - 不在初始卡组
        # 308 千人千面 (Legendary) - 不在初始卡组
    })
    
    return career


def create_farmer_career() -> Career:
    """创建农民职业"""
    career = Career(
        career_type=CareerType.FARMER,
        name="农民",
        description="深耕沃土的耕作者，擅长生存和资源管理",
        hit_dice_type=10  # d10生命骰
    )
    
    # 被动1：深耕沃土
    passive1 = CareerPassive(
        name="深耕沃土",
        description="打出带[生存]标签的卡牌时，目标获得的治疗/格挡值+2。打出带[群体]标签的卡牌时，作用范围+1（仅对农民自身生效）",
        career_type=CareerType.FARMER,
        effect_handler="farmer_deep_plow_handler",
        required_cards=["粮草调度"]
    )
    career.add_passive(passive1)
    
    # 特殊卡牌
    career.special_cards = ["粮草调度"]
    
    # 初始卡组配置（1~6号卡分别有3、3、2、2、1、1张，共12张；7~8号Legendary卡不在初始卡组）
    career.set_initial_deck({
        "坚韧不拔": 3,         # 401 - Common
        "大地守护": 3,         # 402 - Common
        "稳健打击": 2,         # 403 - Common
        "田间陷阱": 2,         # 404 - Uncommon
        "群体鼓舞": 1,         # 405 - Uncommon
        "丰收之击": 1          # 406 - Rare
        # 407 丰收祭典 (Rare) - 不在初始卡组
        # 408 沃土之魂 (Legendary) - 不在初始卡组
    })
    
    return career


def create_scholar_career() -> Career:
    """创建游学青年职业"""
    career = Career(
        career_type=CareerType.SCHOLAR,
        name="游学青年",
        description="博闻强记的学者，擅长知识和法术",
        hit_dice_type=6  # d6生命骰
    )
    
    # 被动1：博闻强记
    passive1 = CareerPassive(
        name="博闻强记",
        description="①每场遭遇首次打出[知识]或[法术]卡时，额外抽1张牌（限1次）；②心智调整值用于社交检定时，+1加值；③大地图移动至知识节点时资源消耗-1",
        career_type=CareerType.SCHOLAR,
        effect_handler="scholar_erudite_handler",
        required_cards=["应急咒文"]
    )
    career.add_passive(passive1)
    
    # 特殊卡牌
    career.special_cards = ["应急咒文"]
    
    # 初始卡组配置（1~6号卡分别有3、3、2、2、1、1张，共12张；7~8号Legendary卡不在初始卡组）
    career.set_initial_deck({
        "奥术冲击": 3,         # 501 - Common
        "知识汲取": 3,         # 502 - Common
        "思维加速": 2,         # 503 - Common
        "秘法屏障": 2,         # 504 - Uncommon
        "精准预言": 1,         # 505 - Uncommon
        "元素共鸣": 1          # 506 - Rare
        # 507 心灵震爆 (Rare) - 不在初始卡组
        # 508 不稳定传送 (Legendary) - 不在初始卡组
    })
    
    return career


# ==================== 职业工厂 ====================

class CareerFactory:
    """职业工厂 - 用于创建和管理职业"""
    
    _careers: Dict[CareerType, Career] = {}
    
    @classmethod
    def initialize(cls):
        """初始化所有职业"""
        cls._careers[CareerType.DRIFTER] = create_drifter_career()
        cls._careers[CareerType.ARTISAN] = create_artisan_career()
        cls._careers[CareerType.PEDLAR] = create_pedlar_career()
        cls._careers[CareerType.FARMER] = create_farmer_career()
        cls._careers[CareerType.SCHOLAR] = create_scholar_career()
    
    @classmethod
    def get_career(cls, career_type: CareerType) -> Optional[Career]:
        """获取职业"""
        if not cls._careers:
            cls.initialize()
        return cls._careers.get(career_type)
    
    @classmethod
    def get_all_careers(cls) -> List[Career]:
        """获取所有职业"""
        if not cls._careers:
            cls.initialize()
        return list(cls._careers.values())
    
    @classmethod
    def save_careers_to_file(cls, filepath: str = "./careers/careers.json"):
        """保存所有职业到文件"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        careers_data = [career.to_dict() for career in cls.get_all_careers()]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(careers_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_careers_from_file(cls, filepath: str = "./careers/careers.json") -> bool:
        """从文件加载职业"""
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            careers_data = json.load(f)
        
        cls._careers.clear()
        for data in careers_data:
            career = Career.from_dict(data)
            cls._careers[career.career_type] = career
        
        return True


# ==================== 便捷函数 ====================

def get_career(career_type: CareerType) -> Optional[Career]:
    """便捷函数：获取职业"""
    return CareerFactory.get_career(career_type)


def get_all_careers() -> List[Career]:
    """便捷函数：获取所有职业"""
    return CareerFactory.get_all_careers()


# ==================== 卡组构建工具函数 ====================

def build_deck_from_config(deck_config: Dict[str, int], cards_db: Dict) -> list:
    """
    根据配置构建卡组（通用函数）
    
    Args:
        deck_config: 卡组配置字典，格式为 {"卡牌名称": 数量}
        cards_db: 卡牌数据库字典
        
    Returns:
        构建好的卡组列表
        
    Example:
        >>> config = {"精准打击": 3, "刺击": 2}
        >>> deck = build_deck_from_config(config, cards_db)
    """
    deck = []
    # print(f"\n[DEBUG] 开始构建卡组")
    # print(f"[DEBUG] 卡组配置: {deck_config}")
    
    for card_name, count in deck_config.items():
        if card_name in cards_db:
            # 添加指定数量的卡牌副本
            for i in range(count):
                card_copy = cards_db[card_name].copy()
                deck.append(card_copy)
                # if i == 0:  # 只打印第一次
                    # print(f"[DEBUG]   ✓ 添加 '{card_name}' x{count}")
        else:
            # print(f"[DEBUG]   ✗ 警告：卡牌 '{card_name}' 不存在于数据库中")
            pass
    
    # print(f"[DEBUG] 卡组构建完成，共 {len(deck)} 张卡牌")
    return deck


def build_career_deck(career_type: CareerType, cards_db: Dict) -> list:
    """
    根据职业类型构建专属卡组（通用函数）
    
    Args:
        career_type: 职业类型枚举
        cards_db: 卡牌数据库字典
        
    Returns:
        构建好的职业专属卡组
        
    Example:
        >>> from career_system import CareerType
        >>> deck = build_career_deck(CareerType.DRIFTER, cards_db)
    """
    # 获取职业信息
    career = CareerFactory.get_career(career_type)
    if not career:
        print(f"警告：未找到职业 {career_type.value}")
        return []
    
    # 使用职业的初始卡组配置构建卡组
    if career.initial_deck_config:
        return build_deck_from_config(career.initial_deck_config, cards_db)
    else:
        print(f"警告：职业 {career.name} 没有配置初始卡组")
        return []

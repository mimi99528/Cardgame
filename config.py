"""
游戏配置和常量定义
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List


# 稀有度枚举
class Rarity(Enum):
    COMMON = 0      # 普通 - 黑色
    UNCOMMON = 1    # 罕见 - 天蓝色
    RARE = 2        # 稀有 - 靛蓝色
    LEGENDARY = 3   # 传说 - 金色


# 稀有度颜色映射
RARITY_COLORS = {
    Rarity.COMMON: (0, 0, 0, 255),          # 黑色
    Rarity.UNCOMMON: (135, 206, 235, 255),  # 天蓝色
    Rarity.RARE: (75, 0, 130, 255),         # 靛蓝色
    Rarity.LEGENDARY: (255, 215, 0, 255),   # 金色
}


# 卡牌类型枚举
class CardType(Enum):
    ATTACK_PHYSICAL = "atk_phy"  # 物理攻击
    ATTACK_MAGICAL = "atk_mag"   # 魔法攻击
    BLOCK = "blk"                # 防御
    HEAL = "hel"                 # 治疗
    SKILL = "skl"                # 技能
    PASSIVE = "pas"              # 被动
    BUFF = "buf"                 # 增益/减益
    MOVE = "move"                # 移动


# 卡牌类型显示名称
CARD_TYPE_NAMES = {
    CardType.ATTACK_PHYSICAL: "物理攻击",
    CardType.ATTACK_MAGICAL: "魔法攻击",
    CardType.BLOCK: "防御",
    CardType.HEAL: "治疗",
    CardType.SKILL: "技能",
    CardType.PASSIVE: "被动",
    CardType.BUFF: "增益",
    CardType.MOVE: "移动",
}


# 目标类型枚举
class TargetType(Enum):
    SELF = "self"           # 自身
    ENEMY = "enemy"         # 敌人
    ALLY = "ally"           # 友军
    ANY = "any"             # 任意目标
    ALL_ENEMIES = "all_enemies"     # 所有敌人
    ALL_ALLIES = "all_allies"       # 所有友军
    ALL = "all"             # 全部（可用于移动等通用场景）


# Buff/Debuff 类型
class BuffType(Enum):
    POISON = "pot"      # 中毒


# 游戏常量
@dataclass
class GameConstants:
    # 窗口设置
    WINDOW_WIDTH: int = 1920
    WINDOW_HEIGHT: int = 1080
    WINDOW_TITLE: str = "卡牌战斗游戏"
    
    # 卡牌尺寸
    CARD_WIDTH: int = 240
    CARD_HEIGHT: int = 320
    CARD_SPACING: int = 20
    
    # UI 布局
    UI_TOP_MARGIN: int = 50
    UI_BOTTOM_MARGIN: int = 50
    HAND_Y_POSITION: int = 120  # 手牌Y位置
    
    # 战斗
    DEFAULT_HAND_SIZE: int = 4
    MAX_BLOCK_RATIO: float = 1.0  # 最大格挡值相对于最大HP的比例
    AI_CARD_PLAY_INTERVAL: float = 0.5  # AI出牌间隔（秒）
    
    # 动画
    CARD_HOVER_OFFSET: int = 60  # 卡牌悬停上移距离
    ANIMATION_SPEED: float = 0.1  # 动画速度


# 实例化常量
CONSTANTS = GameConstants()

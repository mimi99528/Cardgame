"""
游戏配置和常量定义
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List
import arcade


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
    ENEMY_LINE = "enemy_line"       # 直线上的敌人
    ALLY_OR_SELF = "ally_or_self"   # 友方或自身


# 卡牌标签枚举 - 基于table-label.csv定义
class CardTag(Enum):
    # 战斗方式标签
    MELEE = "近战"              # 邻格物理攻击
    RANGED = "远程"             # 跨格攻击
    SPELL = "法术"              # 消耗MP的超自然行动
    CONTROL = "控制"            # 推拉、定身、减速、地形改变
    DISRUPT = "干扰"            # 降属性、劣势、沉默、打断
    COUNTER = "反击"            # 响应敌方行动的触发式效果
    ARMOR_PIERCE = "破甲"       # 削减或无视格挡值
    BLOCK = "格挡"              # 生成/恢复格挡值或提供防御加成
    FORMATION = "阵型"          # 依赖邻格、连线、朝向的协同效果
    STEALTH = "潜行"            # 降仇恨、先攻优势、规避遭遇
    
    # 功能效果标签
    HEALING = "治疗"            # 恢复体力(HP)或移除轻伤
    PURIFY = "净化"             # 移除毒素/疾病/诅咒等状态
    BUFF = "增益"               # 临时属性/检定/资源加成
    DEBUFF = "状态"             # 施加或交互Debuff/伤势
    RESOURCE = "资源"           # 抽牌、回MP、生成临时行动点
    EQUIPMENT_INTERACT = "装备交互"  # 触发装备特效、临时附魔、槽位联动
    SUSTAIN = "续航"            # 生命骰恢复、长休优化、食物/时间管理
    
    # 场景应用标签
    COMBAT = "战斗"             # 战棋场景核心行动
    EXPLORATION = "探索"        # 节点调查、场景交互、解谜
    SOCIAL = "社交"             # NPC对话、阵营交互、谈判/威胁
    MOVEMENT = "移动"           # 大地图节点移动或战棋位移
    UNIVERSAL = "泛用"          # 全场景通用或效果高度自适应
    
    # 属性绑定标签
    STRENGTH = "力量"           # Strength
    DEXTERITY = "敏捷"          # Agility
    INTELLIGENCE = "心智"       # Intellect
    CHARISMA = "魅力"           # Charm
    LUCK = "幸运"               # Luck
    
    # 技能类型标签
    INTELLIGENCE_SKILL = "情报"      # 揭示节点状态、敌人弱点、隐藏路线
    DECEPTION = "欺诈"               # 伪装、bluff、诱导、黑市交易
    KNOWLEDGE = "知识"               # 古代文献、魔法理论、仪式解读
    ENVIRONMENT = "环境互动"         # 操纵场景物、点燃/冻结/破坏地形
    TRAP = "陷阱"                    # 布置、侦测、触发或拆解陷阱
    FATE = "命运"                    # 绑定执念、世界记忆、周目继承
    RISK = "风险"                    # 高方差、可能反噬、依赖暗骰
    SURVIVAL = "生存"                # 应对瘟疫、饥饿、恶劣天气、长途跋涉
    
    # 目标范围标签
    SINGLE = "单体"              # 指定单一目标（敌/友/NPC）
    AOE = "群体"                 # 扇形/圆形/直线多目标
    SELF_ONLY = "自身"           # 仅影响使用者
    FRIENDLY = "友方"            # 仅影响队友或召唤物
    TERRAIN = "地形"             # 影响瓦片/节点状态（创造区域效果）
    
    # 伤害类型标签
    PHYSICAL_DAMAGE = "物理"     # 物理伤害
    FIRE_DAMAGE = "火焰"         # 火焰伤害
    ICE_DAMAGE = "冰霜"          # 冰霜伤害
    LIGHTNING_DAMAGE = "雷电"    # 雷电伤害
    SHADOW_DAMAGE = "暗影"       # 暗影伤害
    HOLY_DAMAGE = "神圣"         # 神圣伤害
    
    # 特殊来源标签
    EQUIPMENT_GRANTED = "赋予"   # 只能由装备赋予的卡牌，不应从卡池抽取


# Buff/Debuff 类型
class BuffType(Enum):
    POISON = "pot"      # 中毒


# 战斗日志级别
class LogLevel(Enum):
    SIMPLE = "simple"       # 简单模式：只显示谁打出了什么牌
    NORMAL = "normal"       # 普通模式：不显示判定细节，只显示结果
    VERBOSE = "verbose"     # 详细模式：显示所有细节


# 游戏常量
@dataclass
class GameConstants:
    # 窗口设置 - 自动检测显示屏大小
    # def __post_init__(self):
    #     """初始化 - 4K UHD (3840x2160)模拟模式"""
    #     # 固定分辨率模式
    #     self.WINDOW_WIDTH = 3840
    #     self.WINDOW_HEIGHT = 2160
    
    WINDOW_WIDTH: int = field(default=1920, init=False)
    WINDOW_HEIGHT: int = field(default=1080, init=False)
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
    
    # 背包系统
    INVENTORY_WIDTH: int = 8      # 背包网格宽度
    INVENTORY_HEIGHT: int = 6     # 背包网格高度
    INVENTORY_MAX_VOLUME: int = 48  # 最大体积（格子数）
    INVENTORY_MAX_WEIGHT: float = 50.0  # 最大重量
    INVENTORY_SLOT_SIZE: int = 50  # 背包格子大小（像素）
    INVENTORY_PADDING: int = 10   # 背包内边距
    
    # 战斗日志级别
    LOG_LEVEL: LogLevel = LogLevel.VERBOSE  # 默认日志级别


# 实例化常量
CONSTANTS = GameConstants()

"""
执念系统模块
提供角色执念的创建、追踪和完成判定功能
"""
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


class ObsessionType(Enum):
    """执念类型枚举"""
    REVENGE = "revenge"              # 复仇：向特定敌人或势力复仇
    KNOWLEDGE = "knowledge"          # 求知：追寻某个知识或秘密
    REDEMPTION = "redemption"        # 救赎：弥补过去的过错
    PROTECTION = "protection"        # 守护：保护某人或某物
    POWER = "power"                  # 力量：追求强大的力量
    FREEDOM = "freedom"              # 自由：摆脱某种束缚
    WEALTH = "wealth"                # 财富：积累财富
    TRUTH = "truth"                  # 真相：揭露某个真相


@dataclass
class ObsessionCondition:
    """执念完成条件"""
    condition_type: str                    # 条件类型：如 "defeat_enemy", "visit_location", "collect_item" 等
    target_id: str                         # 目标ID（敌人ID、地点ID、物品ID等）
    description: str                       # 条件描述
    progress: int = 0                      # 当前进度
    required_progress: int = 1             # 需要的进度
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "condition_type": self.condition_type,
            "target_id": self.target_id,
            "description": self.description,
            "progress": self.progress,
            "required_progress": self.required_progress
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ObsessionCondition':
        """从字典反序列化"""
        return ObsessionCondition(
            condition_type=data["condition_type"],
            target_id=data["target_id"],
            description=data["description"],
            progress=data.get("progress", 0),
            required_progress=data.get("required_progress", 1)
        )
    
    def check_completion(self) -> bool:
        """检查条件是否完成"""
        return self.progress >= self.required_progress
    
    def update_progress(self, amount: int = 1):
        """更新进度"""
        self.progress += amount


@dataclass
class ObsessionReward:
    """执念完成奖励"""
    reward_type: str                       # 奖励类型：如 "stat_bonus", "special_card", "title" 等
    value: Any                             # 奖励值
    description: str                       # 奖励描述
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "reward_type": self.reward_type,
            "value": self.value,
            "description": self.description
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ObsessionReward':
        """从字典反序列化"""
        return ObsessionReward(
            reward_type=data["reward_type"],
            value=data["value"],
            description=data["description"]
        )


@dataclass
class Obsession:
    """执念定义"""
    obsession_id: str                      # 执念唯一ID
    name: str                              # 执念名称
    description: str                       # 执念描述
    obsession_type: ObsessionType          # 执念类型
    conditions: List[ObsessionCondition] = field(default_factory=list)  # 完成条件列表
    rewards: List[ObsessionReward] = field(default_factory=list)        # 完成奖励列表
    is_completed: bool = False             # 是否已完成
    completion_text: str = ""              # 完成时的文本描述
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "obsession_id": self.obsession_id,
            "name": self.name,
            "description": self.description,
            "obsession_type": self.obsession_type.value,
            "conditions": [c.to_dict() for c in self.conditions],
            "rewards": [r.to_dict() for r in self.rewards],
            "is_completed": self.is_completed,
            "completion_text": self.completion_text
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Obsession':
        """从字典反序列化"""
        obsession = Obsession(
            obsession_id=data["obsession_id"],
            name=data["name"],
            description=data["description"],
            obsession_type=ObsessionType(data["obsession_type"]),
            is_completed=data.get("is_completed", False),
            completion_text=data.get("completion_text", "")
        )
        
        # 反序列化条件
        if "conditions" in data:
            obsession.conditions = [
                ObsessionCondition.from_dict(c) for c in data["conditions"]
            ]
        
        # 反序列化奖励
        if "rewards" in data:
            obsession.rewards = [
                ObsessionReward.from_dict(r) for r in data["rewards"]
            ]
        
        return obsession
    
    def check_all_conditions(self) -> bool:
        """检查所有条件是否完成"""
        if not self.conditions:
            return False
        
        return all(condition.check_completion() for condition in self.conditions)
    
    def update_condition_progress(self, condition_type: str, target_id: str, amount: int = 1):
        """
        更新特定条件的进度
        
        Args:
            condition_type: 条件类型
            target_id: 目标ID
            amount: 进度增加量
        """
        for condition in self.conditions:
            if condition.condition_type == condition_type and condition.target_id == target_id:
                condition.update_progress(amount)
                break
    
    def get_progress_percentage(self) -> float:
        """获取完成进度百分比"""
        if not self.conditions:
            return 0.0
        
        completed = sum(1 for c in self.conditions if c.check_completion())
        return (completed / len(self.conditions)) * 100


class ObsessionManager:
    """执念管理器 - 管理所有预设执念的加载和查询"""
    
    def __init__(self):
        self.obsessions: Dict[str, Obsession] = {}
    
    def load_from_file(self, filepath: str):
        """从JSON文件加载执念定义"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # 列表格式
            for obsession_data in data:
                obsession = Obsession.from_dict(obsession_data)
                self.obsessions[obsession.obsession_id] = obsession
        else:
            # 单个执念
            obsession = Obsession.from_dict(data)
            self.obsessions[obsession.obsession_id] = obsession
    
    def save_to_file(self, filepath: str):
        """保存所有执念到JSON文件"""
        data = [obsession.to_dict() for obsession in self.obsessions.values()]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_obsession(self, obsession_id: str) -> Optional[Obsession]:
        """根据ID获取执念"""
        return self.obsessions.get(obsession_id)
    
    def add_obsession(self, obsession: Obsession):
        """添加执念"""
        self.obsessions[obsession.obsession_id] = obsession
    
    def remove_obsession(self, obsession_id: str):
        """移除执念"""
        if obsession_id in self.obsessions:
            del self.obsessions[obsession_id]
    
    def get_all_obsessions(self) -> List[Obsession]:
        """获取所有执念"""
        return list(self.obsessions.values())
    
    def get_obsessions_by_type(self, obsession_type: ObsessionType) -> List[Obsession]:
        """根据类型获取执念列表"""
        return [
            obs for obs in self.obsessions.values()
            if obs.obsession_type == obsession_type
        ]
    
    def clear(self):
        """清空所有执念"""
        self.obsessions.clear()


# ==================== 示例执念创建函数 ====================

def create_example_obsessions() -> List[Obsession]:
    """创建示例执念"""
    obsessions = []
    
    # 1. 复仇执念
    revenge_obsession = Obsession(
        obsession_id="obs_revenge_001",
        name="血债血偿",
        description="你的家人被强盗杀害，你发誓要消灭所有强盗团伙，为家人报仇。",
        obsession_type=ObsessionType.REVENGE,
        conditions=[
            ObsessionCondition(
                condition_type="defeat_enemy",
                target_id="bandit_leader",
                description="击败强盗首领",
                required_progress=1
            ),
            ObsessionCondition(
                condition_type="defeat_enemy",
                target_id="bandit_group",
                description="消灭3个强盗团伙",
                progress=0,
                required_progress=3
            )
        ],
        rewards=[
            ObsessionReward(
                reward_type="stat_bonus",
                value={"strength": 2},
                description="力量+2"
            ),
            ObsessionReward(
                reward_type="special_card",
                value="复仇之刃",
                description="获得特殊卡牌「复仇之刃」"
            )
        ],
        completion_text="你终于完成了复仇，家人的在天之灵可以安息了。"
    )
    obsessions.append(revenge_obsession)
    
    # 2. 求知执念
    knowledge_obsession = Obsession(
        obsession_id="obs_knowledge_001",
        name="古代秘辛",
        description="你一直在寻找失落的古代文明知识，相信其中隐藏着改变世界的力量。",
        obsession_type=ObsessionType.KNOWLEDGE,
        conditions=[
            ObsessionCondition(
                condition_type="visit_location",
                target_id="ancient_ruins",
                description="探索古代遗迹",
                required_progress=1
            ),
            ObsessionCondition(
                condition_type="collect_item",
                target_id="ancient_tome",
                description="收集3本古代典籍",
                progress=0,
                required_progress=3
            ),
            ObsessionCondition(
                condition_type="complete_check",
                target_id="intelligence_check_hard",
                description="通过一次困难的心智检定",
                required_progress=1
            )
        ],
        rewards=[
            ObsessionReward(
                reward_type="stat_bonus",
                value={"intelligence": 2},
                description="心智+2"
            ),
            ObsessionReward(
                reward_type="special_card",
                value="古代智慧",
                description="获得特殊卡牌「古代智慧」"
            )
        ],
        completion_text="你揭开了古代文明的秘密，获得了无价的知识。"
    )
    obsessions.append(knowledge_obsession)
    
    # 3. 救赎执念
    redemption_obsession = Obsession(
        obsession_id="obs_redemption_001",
        name="赎罪之路",
        description="你曾经犯下大错，现在希望通过帮助他人来弥补过去的过错。",
        obsession_type=ObsessionType.REDEMPTION,
        conditions=[
            ObsessionCondition(
                condition_type="help_npc",
                target_id="villager",
                description="帮助10个村民",
                progress=0,
                required_progress=10
            ),
            ObsessionCondition(
                condition_type="complete_quest",
                target_id="rescue_mission",
                description="完成5次救援任务",
                progress=0,
                required_progress=5
            )
        ],
        rewards=[
            ObsessionReward(
                reward_type="stat_bonus",
                value={"charisma": 2},
                description="魅力+2"
            ),
            ObsessionReward(
                reward_type="title",
                value="赎罪者",
                description="获得称号「赎罪者」"
            )
        ],
        completion_text="你通过无数善行洗清了自己的罪孽，内心终于得到了平静。"
    )
    obsessions.append(redemption_obsession)
    
    # 4. 守护执念
    protection_obsession = Obsession(
        obsession_id="obs_protection_001",
        name="永恒守护",
        description="你发誓要保护一个重要的地方或人物，不让其受到任何伤害。",
        obsession_type=ObsessionType.PROTECTION,
        conditions=[
            ObsessionCondition(
                condition_type="defend_location",
                target_id="sacred_temple",
                description="成功守护圣地10次",
                progress=0,
                required_progress=10
            ),
            ObsessionCondition(
                condition_type="defeat_enemy",
                target_id="temple_invader",
                description="击败20个入侵者",
                progress=0,
                required_progress=20
            )
        ],
        rewards=[
            ObsessionReward(
                reward_type="stat_bonus",
                value={"dexterity": 2, "strength": 1},
                description="敏捷+2，力量+1"
            ),
            ObsessionReward(
                reward_type="special_card",
                value="守护誓言",
                description="获得特殊卡牌「守护誓言」"
            )
        ],
        completion_text="你成功地守护了圣地，成为了传说中的守护者。"
    )
    obsessions.append(protection_obsession)
    
    # 5. 力量执念
    power_obsession = Obsession(
        obsession_id="obs_power_001",
        name="力量巅峰",
        description="你渴望达到力量的巅峰，成为无人能敌的存在。",
        obsession_type=ObsessionType.POWER,
        conditions=[
            ObsessionCondition(
                condition_type="defeat_enemy",
                target_id="boss_enemy",
                description="击败5个Boss级敌人",
                progress=0,
                required_progress=5
            ),
            ObsessionCondition(
                condition_type="reach_level",
                target_id="level_10",
                description="达到10级",
                required_progress=1
            ),
            ObsessionCondition(
                condition_type="win_battle",
                target_id="difficult_battle",
                description="赢得20场战斗",
                progress=0,
                required_progress=20
            )
        ],
        rewards=[
            ObsessionReward(
                reward_type="stat_bonus",
                value={"strength": 3, "dexterity": 2},
                description="力量+3，敏捷+2"
            ),
            ObsessionReward(
                reward_type="special_card",
                value="力量觉醒",
                description="获得特殊卡牌「力量觉醒」"
            )
        ],
        completion_text="你达到了力量的巅峰，成为了传说中的强者。"
    )
    obsessions.append(power_obsession)
    
    # 6. 祭坛相关执念（用于测试叙事检定）
    altar_obsession = Obsession(
        obsession_id="obs_altar_001",
        name="神谕追寻者",
        description="你相信古老祭坛中隐藏着神的旨意，决心解读其中的奥秘。",
        obsession_type=ObsessionType.TRUTH,
        conditions=[
            ObsessionCondition(
                condition_type="visit_location",
                target_id="altar_site",
                description="访问祭坛遗址",
                required_progress=1
            ),
            ObsessionCondition(
                condition_type="complete_check",
                target_id="altar_intelligence_check",
                description="在祭坛通过困难心智检定",
                required_progress=1
            ),
            ObsessionCondition(
                condition_type="make_choice",
                target_id="altar_sacrifice",
                description="在祭坛做出牺牲选择",
                required_progress=1
            )
        ],
        rewards=[
            ObsessionReward(
                reward_type="stat_bonus",
                value={"intelligence": 1, "luck": 2},
                description="心智+1，幸运+2"
            ),
            ObsessionReward(
                reward_type="special_card",
                value="神谕启示",
                description="获得特殊卡牌「神谕启示」"
            )
        ],
        completion_text="你解读了神谕，获得了神的眷顾。"
    )
    obsessions.append(altar_obsession)
    
    return obsessions


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("执念系统测试")
    print("=" * 60)
    
    # 创建示例执念
    obsessions = create_example_obsessions()
    
    # 创建执念管理器
    manager = ObsessionManager()
    for obsession in obsessions:
        manager.add_obsession(obsession)
    
    # 保存执念
    manager.save_to_file("obsessions.json")
    print("\n✓ 已保存示例执念到 obsessions.json")
    
    # 重新加载执念
    manager2 = ObsessionManager()
    manager2.load_from_file("obsessions.json")
    print("✓ 已从文件加载执念")
    
    # 获取执念
    obsession = manager2.get_obsession("obs_revenge_001")
    if obsession:
        print(f"\n执念名称: {obsession.name}")
        print(f"执念描述: {obsession.description}")
        print(f"执念类型: {obsession.obsession_type.value}")
        print(f"条件数量: {len(obsession.conditions)}")
        print(f"奖励数量: {len(obsession.rewards)}")
        
        for i, condition in enumerate(obsession.conditions, 1):
            print(f"\n条件{i}: {condition.description}")
            print(f"  类型: {condition.condition_type}")
            print(f"  目标: {condition.target_id}")
            print(f"  进度: {condition.progress}/{condition.required_progress}")
    
    print("\n" + "=" * 60)

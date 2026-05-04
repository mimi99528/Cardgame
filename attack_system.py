"""
攻击判定系统 - 实现2d10+加值 vs DN的判定框架
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

from dice_system import DiceCheck


class AttackOutcome(Enum):
    """攻击结果类型"""
    CRITICAL_SUCCESS = "大成功"  # 结果 >= DN + 8
    SUCCESS = "成功"            # 结果 >= DN
    PARTIAL_SUCCESS = "半成功"  # DN - 4 <= 结果 < DN
    FAILURE = "失败"           # 结果 < DN - 4
    CRITICAL_FAILURE = "大失败" # 结果 <= DN - 9


@dataclass
class AttackResult:
    """攻击判定结果"""
    outcome: AttackOutcome
    dice_results: Tuple[int, int]  # 两个骰子的结果
    total_roll: int  # 骰子总和
    modifier: int  # 加值
    final_result: int  # 最终结果
    difficulty: int  # 难度值(DN)
    base_damage: int  # 基础伤害
    actual_damage: int  # 实际伤害
    extra_effects: list = None  # 额外效果列表
    
    def __post_init__(self):
        if self.extra_effects is None:
            self.extra_effects = []
    
    def __str__(self):
        return (f"攻击判定: {self.outcome.value}\n"
                f"  骰子: {self.dice_results[0]} + {self.dice_results[1]} = {self.total_roll}\n"
                f"  加值: {self.modifier:+d}\n"
                f"  最终结果: {self.final_result} vs DN {self.difficulty}\n"
                f"  伤害: {self.base_damage} -> {self.actual_damage}\n"
                f"  额外效果: {', '.join(self.extra_effects) if self.extra_effects else '无'}")


def calculate_attack_difficulty(attacker, weapon=None) -> int:
    """
    计算攻击的难度值(DN)
    
    Args:
        attacker: 攻击者实体
        weapon: 使用的武器（可选）
    
    Returns:
        难度值(DN)
    """
    # 基础DN设为10，可以根据实际情况调整
    base_dn = 10
    
    # 如果有武器，可以调整DN
    if weapon and hasattr(weapon, 'attack_modifier'):
        base_dn -= weapon.attack_modifier
    
    return base_dn


def perform_attack_check(attacker, target, base_damage: int, weapon=None) -> AttackResult:
    """
    执行攻击判定
    
    Args:
        attacker: 攻击者实体
        target: 目标实体
        base_damage: 基础伤害
        weapon: 使用的武器（可选）
    
    Returns:
        AttackResult 对象
    """
    # 计算DN
    difficulty = calculate_attack_difficulty(attacker, weapon)
    
    # 计算加值（来自武器和属性）
    modifier = 0
    if weapon and hasattr(weapon, 'attack_modifier'):
        modifier += weapon.attack_modifier
    
    # 执行检定
    check = DiceCheck(difficulty=difficulty, modifier=modifier)
    result = check.roll()
    
    # 根据结果类型计算实际伤害和额外效果
    outcome = AttackOutcome(result.outcome)
    actual_damage = base_damage
    extra_effects = []
    
    if outcome == AttackOutcome.CRITICAL_SUCCESS:
        # 大成功：伤害翻倍，可选择额外效果
        actual_damage = base_damage * 2
        extra_effects.append("伤害翻倍")
        # 可以添加击退、缴械等效果
        extra_effects.append("可选择额外效果（击退/缴械/追加攻击）")
    
    elif outcome == AttackOutcome.SUCCESS:
        # 成功：标准伤害
        actual_damage = base_damage
    
    elif outcome == AttackOutcome.PARTIAL_SUCCESS:
        # 半成功：一半伤害或附带战术状态
        actual_damage = base_damage // 2
        extra_effects.append("半伤或战术状态（擦伤/火力压制）")
    
    elif outcome == AttackOutcome.FAILURE:
        # 失败：未命中
        actual_damage = 0
    
    elif outcome == AttackOutcome.CRITICAL_FAILURE:
        # 大失败：武器卡壳、误伤队友或暴露破绽
        actual_damage = 0
        extra_effects.append("大失败！武器卡壳/误伤/暴露破绽")
    
    return AttackResult(
        outcome=outcome,
        dice_results=(result.dice_results[0], result.dice_results[1]),
        total_roll=result.total,
        modifier=result.modifier,
        final_result=result.final_result,
        difficulty=result.difficulty,
        base_damage=base_damage,
        actual_damage=actual_damage,
        extra_effects=extra_effects
    )


# 示例用法
if __name__ == "__main__":
    print("=" * 60)
    print("攻击判定系统演示")
    print("=" * 60)
    
    # 模拟攻击者和目标
    class MockEntity:
        def __init__(self, name):
            self.name = name
    
    class MockWeapon:
        def __init__(self, name, attack_mod):
            self.name = name
            self.attack_modifier = attack_mod
    
    attacker = MockEntity("玩家")
    target = MockEntity("敌人")
    weapon = MockWeapon("手半剑", 2)
    
    # 执行几次攻击判定
    print("\n示例攻击判定:")
    for i in range(5):
        result = perform_attack_check(attacker, target, base_damage=15, weapon=weapon)
        print(f"\n第{i+1}次攻击:")
        print(result)
        print("-" * 40)
    
    print("\n" + "=" * 60)

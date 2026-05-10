"""
掷骰子系统 - 提供任意掷骰和检定功能
"""
import random
from dataclasses import dataclass
from typing import List, Tuple


def roll_dice(num_dice: int, sides: int) -> List[int]:
    """
    任意掷骰函数
    
    Args:
        num_dice: 骰子数量
        sides: 每个骰子的面数
        
    Returns:
        每个骰子的结果列表
    """
    return [random.randint(1, sides) for _ in range(num_dice)]


def roll_dice_sum(num_dice: int, sides: int) -> int:
    """
    掷骰并返回总和
    
    Args:
        num_dice: 骰子数量
        sides: 每个骰子的面数
        
    Returns:
        所有骰子的总和
    """
    return sum(roll_dice(num_dice, sides))


def roll_dice_from_expression(dice_expr: str) -> List[int]:
    """
    从骰子表达式掷骰
    
    Args:
        dice_expr: 骰子表达式，如 "1d4", "2d6", "3d8", "2d10dh1", "2d10dl1" 等
        dhX: Drop Highest X - 去掉X个最高值（取劣势，保留较低的值）
        dlX: Drop Lowest X - 去掉X个最低值（取优势，保留较高的值）
        
    Returns:
        每个骰子的结果列表
    """
    try:
        # 解析表达式，格式为 "NdM" 或 "NdMdhX" 或 "NdMdlX"
        dice_expr = dice_expr.lower().strip()
        
        # 检查是否有dh或dl后缀
        drop_mode = None
        drop_count = 0
        
        if 'dh' in dice_expr:
            parts = dice_expr.split('dh')
            base_expr = parts[0]
            drop_mode = 'highest'
            drop_count = int(parts[1]) if len(parts) > 1 else 1
        elif 'dl' in dice_expr:
            parts = dice_expr.split('dl')
            base_expr = parts[0]
            drop_mode = 'lowest'
            drop_count = int(parts[1]) if len(parts) > 1 else 1
        else:
            base_expr = dice_expr
        
        # 解析基础骰子表达式 "NdM"
        parts = base_expr.split('d')
        if len(parts) == 2:
            num_dice = int(parts[0])
            sides = int(parts[1])
            results = roll_dice(num_dice, sides)
            
            # 应用取优势/劣势逻辑
            if drop_mode and drop_count > 0 and len(results) > drop_count:
                if drop_mode == 'highest':
                    # dh: 去掉最高的X个（取劣势，保留较低的）
                    results.sort()  # 升序排序
                    results = results[:len(results) - drop_count]  # 保留前面的（较小的）
                elif drop_mode == 'lowest':
                    # dl: 去掉最低的X个（取优势，保留较高的）
                    results.sort(reverse=True)  # 降序排序
                    results = results[:len(results) - drop_count]  # 保留前面的（较大的）
            
            return results
        else:
            return []
    except (ValueError, IndexError):
        return []


def roll_dice_sum_from_expression(dice_expr: str) -> int:
    """
    从骰子表达式掷骰并返回总和
    
    Args:
        dice_expr: 骰子表达式，如 "1d4", "2d6", "3d8", "2d10dh1", "2d10dl1" 等
        dhX: Drop Highest X - 去掉X个最高值（取劣势，保留较低的值）
        dlX: Drop Lowest X - 去掉X个最低值（取优势，保留较高的值）
        
    Returns:
        骰子结果的总和
    """
    return sum(roll_dice_from_expression(dice_expr))


@dataclass
class CheckResult:
    """检定结果类"""
    dice_results: List[int]  # 每个骰子的结果
    total: int  # 骰子总和（不含加值）
    modifier: int  # 加值
    final_result: int  # 最终结果（含加值）
    difficulty: int  # 难度值 (DN)
    outcome: str  # 结果类型：大成功/成功/半成功/失败/大失败
    
    def __str__(self):
        return (f"检定结果: 骰子={self.dice_results}, 总和={self.total}, "
                f"加值={self.modifier:+d}, 最终结果={self.final_result}, "
                f"难度={self.difficulty}, 判定={self.outcome}")


class DiceCheck:
    """
    检定类 - 使用2d10进行检定
    
    判定规则：
    - 大成功: 结果 >= DN + 8
    - 成功: 结果 >= DN
    - 半成功: DN - 4 <= 结果 < DN
    - 失败: 结果 < DN - 4
    - 大失败: 结果 <= DN - 9
    
    支持取优势/劣势：
    - check_advantage="dl1": 攻击判定取优势（去掉最低值）
    - check_disadvantage="dh1": 攻击判定取劣势（去掉最高值）
    """
    
    def __init__(self, difficulty: int, modifier: int = 0, 
                 check_advantage: str = None, check_disadvantage: str = None):
        """
        初始化检定
        
        Args:
            difficulty: 难度值 (DN)
            modifier: 加值（默认为0）
            check_advantage: 攻击判定取优势表达式，如 "dl1"（可选）
            check_disadvantage: 攻击判定取劣势表达式，如 "dh1"（可选）
        """
        self.difficulty = difficulty
        self.modifier = modifier
        self.check_advantage = check_advantage
        self.check_disadvantage = check_disadvantage
    
    def roll(self) -> CheckResult:
        """
        执行检定
        
        Returns:
            CheckResult 对象，包含检定结果
        """
        # 掷2个10面骰
        dice_results = roll_dice(2, 10)
        
        # 应用攻击判定取优势/劣势
        if self.check_advantage:
            # 解析dlX表达式
            drop_count = int(self.check_advantage[2:]) if len(self.check_advantage) > 2 else 1
            # 取优势：掷3个骰子，去掉最低的drop_count个，保留较高的
            dice_results = roll_dice(2 + drop_count, 10)
            if drop_count > 0 and len(dice_results) > drop_count:
                # dl: 去掉最低值，保留较高的
                dice_results.sort(reverse=True)  # 降序排序
                dice_results = dice_results[:len(dice_results) - drop_count]
        elif self.check_disadvantage:
            # 解析dhX表达式
            drop_count = int(self.check_disadvantage[2:]) if len(self.check_disadvantage) > 2 else 1
            # 取劣势：掷3个骰子，去掉最高的drop_count个，保留较低的
            dice_results = roll_dice(2 + drop_count, 10)
            if drop_count > 0 and len(dice_results) > drop_count:
                # dh: 去掉最高值，保留较低的
                dice_results.sort()  # 升序排序
                dice_results = dice_results[:len(dice_results) - drop_count]
        
        total = sum(dice_results)
        final_result = total + self.modifier
        
        # 判定结果
        outcome = self._determine_outcome(final_result)
        
        return CheckResult(
            dice_results=dice_results,
            total=total,
            modifier=self.modifier,
            final_result=final_result,
            difficulty=self.difficulty,
            outcome=outcome
        )
    
    def _determine_outcome(self, final_result: int) -> str:
        """
        根据最终结果判定结果类型
        
        Args:
            final_result: 最终结果（含加值）
            
        Returns:
            结果类型字符串
        """
        if final_result >= self.difficulty + 8:
            return "大成功"
        elif final_result >= self.difficulty:
            return "成功"
        elif final_result >= self.difficulty - 4:
            return "半成功"
        elif final_result > self.difficulty - 9:
            return "失败"
        else:  # final_result <= difficulty - 9
            return "大失败"
    
    @staticmethod
    def calculate_probability(difficulty: int, modifier: int = 0, 
                             simulations: int = 100000) -> dict:
        """
        计算各种结果的概率
        
        Args:
            difficulty: 难度值
            modifier: 加值
            simulations: 模拟次数
            
        Returns:
            包含各结果概率的字典
        """
        outcomes = {"大成功": 0, "成功": 0, "半成功": 0, "失败": 0, "大失败": 0}
        
        check = DiceCheck(difficulty, modifier)
        for _ in range(simulations):
            result = check.roll()
            outcomes[result.outcome] += 1
        
        # 转换为概率
        probabilities = {k: v / simulations for k, v in outcomes.items()}
        return probabilities


# 示例用法
if __name__ == "__main__":
    print("=" * 60)
    print("掷骰子系统演示")
    print("=" * 60)
    
    # 演示任意掷骰
    print("\n1. 任意掷骰示例:")
    print(f"   3d6: {roll_dice(3, 6)}")
    print(f"   2d10: {roll_dice(2, 10)}")
    print(f"   1d20: {roll_dice(1, 20)}")
    
    # 演示检定
    print("\n2. 检定示例 (DN=15, 加值=+2):")
    check = DiceCheck(difficulty=15, modifier=2)
    for i in range(5):
        result = check.roll()
        print(f"   第{i+1}次: {result}")
    
    # 演示概率计算
    print("\n3. 概率计算示例 (DN=15, 无加值):")
    probs = DiceCheck.calculate_probability(difficulty=15, modifier=0, simulations=50000)
    for outcome, prob in probs.items():
        print(f"   {outcome}: {prob:.2%}")
    
    print("\n" + "=" * 60)

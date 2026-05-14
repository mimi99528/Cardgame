"""
地图资源管理系统
管理玩家在大地图上的资源（食物、时间等）和移动消耗
"""
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field


@dataclass
class PlayerResources:
    """玩家资源管理类"""
    
    # 食物相关
    food_units: int = 10  # 当前食物单位（FU）
    max_food_units: int = 20  # 最大食物携带量
    
    # 时间相关  
    current_day: int = 1  # 当前天数
    current_time: int = 0  # 当天时间（0-23小时）
    
    # 其他资源
    gold: int = 50  # 金币
    luck_points: int = 3  # 幸运点数
    
    def consume_food(self, amount: int) -> Tuple[bool, str]:
        """
        消耗食物
        
        Args:
            amount: 要消耗的食物单位数量
            
        Returns:
            (是否成功, 消息)
        """
        if self.food_units >= amount:
            self.food_units -= amount
            return True, f"消耗了 {amount} FU 食物"
        else:
            return False, f"食物不足！当前: {self.food_units} FU, 需要: {amount} FU"
    
    def add_food(self, amount: int) -> Tuple[bool, str]:
        """
        添加食物
        
        Args:
            amount: 要添加的食物单位数量
            
        Returns:
            (是否成功, 消息)
        """
        if self.food_units + amount <= self.max_food_units:
            self.food_units += amount
            return True, f"获得了 {amount} FU 食物"
        else:
            actual_add = self.max_food_units - self.food_units
            self.food_units = self.max_food_units
            return True, f"获得了 {actual_add} FU 食物（已达上限）"
    
    def advance_time(self, hours: int):
        """
        推进时间
        
        Args:
            hours: 要推进的小时数
        """
        self.current_time += hours
        
        # 处理天数变化
        while self.current_time >= 24:
            self.current_time -= 24
            self.current_day += 1
    
    def get_time_string(self) -> str:
        """获取时间字符串表示"""
        return f"第{self.current_day}天 {self.current_time:02d}:00"
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            "food_units": self.food_units,
            "max_food_units": self.max_food_units,
            "current_day": self.current_day,
            "current_time": self.current_time,
            "gold": self.gold,
            "luck_points": self.luck_points
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'PlayerResources':
        """从字典反序列化"""
        resources = PlayerResources()
        resources.food_units = data.get("food_units", 10)
        resources.max_food_units = data.get("max_food_units", 20)
        resources.current_day = data.get("current_day", 1)
        resources.current_time = data.get("current_time", 0)
        resources.gold = data.get("gold", 50)
        resources.luck_points = data.get("luck_points", 3)
        return resources


class MapResourceManager:
    """地图资源管理器 - 处理节点移动时的资源消耗"""
    
    def __init__(self, player_resources: PlayerResources):
        self.resources = player_resources
        self.movement_log: List[str] = []  # 移动日志
    
    def try_move_to_node(self, target_node, edge_cost: int = 1) -> Tuple[bool, str]:
        """
        尝试移动到目标节点
        
        Args:
            target_node: 目标节点对象（需要有food_cost和time_cost属性）
            edge_cost: 边的移动成本（默认1）
            
        Returns:
            (是否成功, 消息)
        """
        messages = []
        
        # 计算总消耗
        food_cost = getattr(target_node, 'food_cost', 1) * edge_cost
        time_cost = getattr(target_node, 'time_cost', 1) * edge_cost
        
        # 检查食物是否足够
        can_consume_food, food_msg = self.resources.consume_food(food_cost)
        if not can_consume_food:
            return False, f"无法移动：{food_msg}"
        
        messages.append(food_msg)
        
        # 推进时间
        self.resources.advance_time(time_cost)
        messages.append(f"时间流逝 {time_cost} 小时")
        
        # 记录日志
        log_entry = f"移动到 {target_node.name} - 消耗 {food_cost} FU, {time_cost} 小时"
        self.movement_log.append(log_entry)
        
        return True, " | ".join(messages)
    
    def rest_at_node(self, hours: int = 8) -> Tuple[bool, str]:
        """
        在节点休息
        
        Args:
            hours: 休息小时数（默认8小时）
            
        Returns:
            (是否成功, 消息)
        """
        # 休息消耗少量食物
        food_cost = max(1, hours // 4)  # 每4小时消耗1 FU
        
        can_consume, msg = self.resources.consume_food(food_cost)
        if not can_consume:
            return False, f"无法休息：{msg}"
        
        # 推进时间
        self.resources.advance_time(hours)
        
        message = f"休息了 {hours} 小时，消耗 {food_cost} FU 食物"
        self.movement_log.append(message)
        
        return True, message
    
    def use_food_item(self, food_name: str, food_value: int = 1) -> Tuple[bool, str]:
        """
        使用食物物品补充食物单位
        
        Args:
            food_name: 食物名称
            food_value: 食物的FU值
            
        Returns:
            (是否成功, 消息)
        """
        success, msg = self.resources.add_food(food_value)
        if success:
            self.movement_log.append(f"食用 {food_name}，获得 {food_value} FU")
        return success, msg
    
    def get_status_summary(self) -> Dict:
        """获取资源状态摘要"""
        return {
            "food": f"{self.resources.food_units}/{self.resources.max_food_units} FU",
            "time": self.resources.get_time_string(),
            "gold": f"{self.resources.gold} G",
            "luck": f"{self.resources.luck_points} LP",
            "recent_moves": self.movement_log[-5:]  # 最近5次移动
        }
    
    def clear_log(self):
        """清空移动日志"""
        self.movement_log.clear()

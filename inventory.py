"""
背包系统模块
包含物品和背包的数据模型
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


def parse_value_or_dice(value) -> float:
    """
    解析数值或骰子表达式
    
    Args:
        value: 可以是数值(int/float)或骰子表达式字符串(如 "2d4+2", "1d6")
        
    Returns:
        解析后的数值(如果是骰子表达式则掷骰)
    """
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, str):
        # 尝试解析骰子表达式
        try:
            from dice_system import roll_dice_sum
            import re
            
            # 匹配骰子表达式，如 "2d4+2", "1d6", "3d8-1"
            match = re.match(r'(\d+)d(\d+)([+-]\d+)?', value)
            if match:
                num_dice = int(match.group(1))
                sides = int(match.group(2))
                modifier = int(match.group(3)) if match.group(3) else 0
                
                dice_result = roll_dice_sum(num_dice, sides)
                return float(dice_result + modifier)
            else:
                # 如果不是骰子表达式，尝试直接转换为数值
                return float(value)
        except (ValueError, AttributeError):
            return 0.0
    else:
        return 0.0


# 物品形状枚举
class ItemShape(Enum):
    """物品在背包中的形状"""
    SINGLE = "single"           # 1x1 单格
    HORIZONTAL_2 = "h2"         # 2x1 横向双格
    VERTICAL_2 = "v2"           # 1x2 纵向双格
    SQUARE_2X2 = "sq2"          # 2x2 方形
    HORIZONTAL_3 = "h3"         # 3x1 横向三格
    L_SHAPE = "l_shape"         # L形（2x2缺一角）


# 物品类型枚举
class ItemType(Enum):
    """物品类型"""
    WEAPON = "weapon"           # 武器
    ARMOR = "armor"             # 防具
    CONSUMABLE = "consumable"   # 消耗品
    MATERIAL = "material"       # 材料
    QUEST = "quest"             # 任务物品
    MISC = "misc"               # 其他


@dataclass
class InventoryItem:
    """背包物品"""
    name: str                   # 物品名称
    item_type: ItemType         # 物品类型
    description: str            # 物品描述
    weight: float = 0.0         # 重量(可以是数值或骰子表达式字符串)
    volume: int = 0             # 占用的体积(格子数)
    shape: ItemShape = ItemShape.SINGLE  # 物品形状
    icon_color: Tuple[int, int, int] = (255, 255, 255)  # 图标颜色(RGB)
    stackable: bool = False     # 是否可堆叠
    stack_count: int = 1        # 堆叠数量
    max_stack: int = 1          # 最大堆叠数
    
    # 物品属性(根据类型不同而不同)
    properties: Dict[str, any] = field(default_factory=dict)
    
    # 使用效果(消耗品和装备)
    use_effects: Dict[str, any] = field(default_factory=dict)  # 例如: {"heal": "2d4+2"} 或 {"equip_slot": "weapon", "equipment_id": 104}
    ap_cost: int = 1  # 使用物品消耗的AP,默认1点
    
    # 唯一ID(用于序列化)
    item_id: Optional[int] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.stackable and self.max_stack < 1:
            self.max_stack = 1
        if not self.stackable:
            self.stack_count = 1
    
    def get_total_weight(self) -> float:
        """获取总重量（考虑堆叠）"""
        return self.weight * self.stack_count
    
    def can_stack_with(self, other: 'InventoryItem') -> bool:
        """判断是否可以与另一个物品堆叠"""
        if not self.stackable or not other.stackable:
            return False
        return (self.name == other.name and 
                self.item_type == other.item_type and
                self.shape == other.shape)
    
    def add_to_stack(self, count: int) -> int:
        """
        添加到堆叠
        
        Args:
            count: 要添加的数量
            
        Returns:
            实际添加的数量
        """
        if not self.stackable:
            return 0
        
        space_available = self.max_stack - self.stack_count
        actual_add = min(count, space_available)
        self.stack_count += actual_add
        return actual_add
    
    def remove_from_stack(self, count: int) -> int:
        """
        从堆叠中移除
        
        Args:
            count: 要移除的数量
            
        Returns:
            实际移除的数量
        """
        actual_remove = min(count, self.stack_count)
        self.stack_count -= actual_remove
        return actual_remove
    
    def copy(self) -> 'InventoryItem':
        """创建副本"""
        from copy import deepcopy
        return deepcopy(self)
    
    def to_dict(self) -> Dict[str, any]:
        """
        将物品转换为字典(用于序列化)
        
        Returns:
            包含物品信息的字典
        """
        return {
            "item_id": self.item_id,
            "name": self.name,
            "item_type": self.item_type.value,
            "description": self.description,
            "weight": self.weight,
            "volume": self.volume,
            "shape": self.shape.value,
            "icon_color": list(self.icon_color),
            "stackable": self.stackable,
            "stack_count": self.stack_count,
            "max_stack": self.max_stack,
            "properties": self.properties.copy(),
            "use_effects": self.use_effects.copy(),
            "ap_cost": self.ap_cost
        }
    
    @staticmethod
    def from_dict(data: Dict[str, any]) -> 'InventoryItem':
        """
        从字典创建物品(用于反序列化)
        
        Args:
            data: 包含物品信息的字典
            
        Returns:
            InventoryItem对象
        """
        # 转换枚举值
        item_type = ItemType(data.get("item_type", "misc"))
        shape = ItemShape(data.get("shape", "single"))
        
        # 转换颜色列表为元组
        icon_color = tuple(data.get("icon_color", [255, 255, 255]))
        
        item = InventoryItem(
            name=data.get("name", "未知物品"),
            item_type=item_type,
            description=data.get("description", ""),
            weight=data.get("weight", 0.0),
            volume=data.get("volume", 0),
            shape=shape,
            icon_color=icon_color,
            stackable=data.get("stackable", False),
            stack_count=data.get("stack_count", 1),
            max_stack=data.get("max_stack", 1),
            properties=data.get("properties", {}),
            use_effects=data.get("use_effects", {}),
            ap_cost=data.get("ap_cost", 1),
            item_id=data.get("item_id")
        )
        
        return item
    
    def __str__(self):
        if self.stackable and self.stack_count > 1:
            return f"{self.name} x{self.stack_count}"
        return self.name
    
    def __repr__(self):
        return f"InventoryItem({self.name}, {self.item_type.value})"


@dataclass
class InventorySlot:
    """背包格子"""
    x: int                      # 格子X坐标
    y: int                      # 格子Y坐标
    item: Optional[InventoryItem] = None  # 格子中的物品
    occupied: bool = False      # 是否被占用


class Inventory:
    """背包系统"""
    
    def __init__(
        self,
        owner_name: str = "",
        grid_width: int = 8,    # 背包网格宽度
        grid_height: int = 6,   # 背包网格高度
        max_volume: int = 48,   # 最大体积（格子数）
        max_weight: float = 50.0  # 最大重量
    ):
        self.owner_name = owner_name
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.max_volume = max_volume
        self.max_weight = max_weight
        
        # 当前状态
        self.current_volume = 0
        self.current_weight = 0.0
        
        # 物品列表（不基于网格位置，用于快速访问）
        self.items: List[InventoryItem] = []
        
        # 网格系统（二维数组）
        self.grid: List[List[Optional[InventoryItem]]] = [
            [None for _ in range(grid_width)] 
            for _ in range(grid_height)
        ]
    
    def can_add_item(self, item: InventoryItem, position: Tuple[int, int] = None) -> Tuple[bool, str]:
        """
        检查是否可以添加物品
        
        Args:
            item: 要添加的物品
            position: 指定位置（可选）
            
        Returns:
            (是否可以添加, 原因说明)
        """
        # 检查重量限制
        if self.current_weight + item.get_total_weight() > self.max_weight:
            return False, f"超重！当前重量: {self.current_weight:.1f}/{self.max_weight:.1f}"
        
        # 检查体积限制
        if self.current_volume + item.volume > self.max_volume:
            return False, f"空间不足！当前体积: {self.current_volume}/{self.max_volume}"
        
        # 如果是指定位置放置，检查该位置是否可用
        if position is not None:
            if not self._can_place_at(item, position[0], position[1]):
                return False, "该位置无法放置此物品"
        
        return True, "可以添加"
    
    def add_item(self, item: InventoryItem, position: Tuple[int, int] = None) -> Tuple[bool, str]:
        """
        添加物品到背包
        
        Args:
            item: 要添加的物品
            position: 指定位置（可选），如果不指定则自动寻找合适位置
            
        Returns:
            (是否成功, 说明)
        """
        # 先检查是否可以添加
        can_add, reason = self.can_add_item(item, position)
        if not can_add:
            return False, reason
        
        # 尝试堆叠
        if item.stackable:
            for existing_item in self.items:
                if existing_item.can_stack_with(item):
                    remaining = item.add_to_stack(item.stack_count)
                    if remaining < item.stack_count:
                        # 部分堆叠成功
                        item.stack_count = remaining
                    else:
                        # 完全堆叠成功
                        self.current_weight += item.get_total_weight()
                        self.current_volume += item.volume
                        self.items.append(item)
                        return True, f"已堆叠到 {existing_item}"
        
        # 寻找放置位置
        if position is None:
            position = self._find_placement_position(item)
        
        if position is None:
            return False, "找不到合适的放置位置"
        
        # 放置物品
        if self._place_item_at(item, position[0], position[1]):
            self.items.append(item)
            self.current_weight += item.get_total_weight()
            self.current_volume += item.volume
            return True, f"已添加 {item}"
        
        return False, "放置失败"
    
    def remove_item(self, item: InventoryItem, count: int = 1) -> Tuple[bool, str]:
        """
        从背包移除物品
        
        Args:
            item: 要移除的物品
            count: 移除数量（仅对可堆叠物品有效）
            
        Returns:
            (是否成功, 说明)
        """
        if item not in self.items:
            return False, "物品不在背包中"
        
        if item.stackable and item.stack_count > count:
            # 部分移除
            removed = item.remove_from_stack(count)
            self.current_weight -= item.weight * removed
            return True, f"移除了 {removed} 个 {item.name}"
        else:
            # 完全移除
            self._remove_item_from_grid(item)
            self.items.remove(item)
            self.current_weight -= item.get_total_weight()
            self.current_volume -= item.volume
            return True, f"移除了 {item}"
    
    def get_item_at(self, x: int, y: int) -> Optional[InventoryItem]:
        """获取指定位置的物品"""
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            return self.grid[y][x]
        return None
    
    def get_items_by_type(self, item_type: ItemType) -> List[InventoryItem]:
        """按类型获取物品"""
        return [item for item in self.items if item.item_type == item_type]
    
    def get_all_items(self) -> List[InventoryItem]:
        """获取所有物品"""
        return self.items.copy()
    
    def clear(self):
        """清空背包"""
        self.items.clear()
        self.current_volume = 0
        self.current_weight = 0.0
        self.grid = [
            [None for _ in range(self.grid_width)] 
            for _ in range(self.grid_height)
        ]
    
    def get_usage_info(self) -> Dict[str, any]:
        """获取背包使用信息"""
        return {
            "volume_used": self.current_volume,
            "volume_max": self.max_volume,
            "volume_percent": (self.current_volume / self.max_volume * 100) if self.max_volume > 0 else 0,
            "weight_used": self.current_weight,
            "weight_max": self.max_weight,
            "weight_percent": (self.current_weight / self.max_weight * 100) if self.max_weight > 0 else 0,
            "item_count": len(self.items),
            "grid_width": self.grid_width,
            "grid_height": self.grid_height
        }
    
    def use_item(self, item: InventoryItem, user_entity=None) -> Tuple[bool, str]:
        """
        使用物品
        
        Args:
            item: 要使用的物品
            user_entity: 使用者实体（用于消耗AP和应用效果）
            
        Returns:
            (是否成功, 说明)
        """
        if item not in self.items:
            return False, "物品不在背包中"
        
        # 检查AP是否足够
        if user_entity and hasattr(user_entity, 'ap'):
            if user_entity.ap < item.ap_cost:
                return False, f"AP不足！需要{item.ap_cost}点，剩余{user_entity.ap}点"
        
        # 根据物品类型执行不同操作
        if item.item_type == ItemType.CONSUMABLE:
            # 消耗品：应用效果
            result = self._apply_consumable_effect(item, user_entity)
            if result[0]:  # 如果成功
                # 减少堆叠数量或移除物品
                if item.stackable and item.stack_count > 1:
                    item.remove_from_stack(1)
                else:
                    self.remove_item(item)
            return result
        
        elif item.item_type == ItemType.WEAPON or item.item_type == ItemType.ARMOR:
            # 装备：穿戴装备
            result = self._equip_item(item, user_entity)
            if result[0]:  # 如果成功
                # 装备不消耗，只是从背包移到装备栏
                pass
            return result
        
        else:
            return False, f"无法使用{item.item_type.value}类型的物品"
    
    def _apply_consumable_effect(self, item: InventoryItem, user_entity) -> Tuple[bool, str]:
        """应用消耗品效果"""
        if not user_entity:
            return False, "没有使用者"
        
        effects = item.use_effects
        results = []
        
        # 治疗效果 - 支持骰子表达式
        if "heal" in effects:
            heal_value = effects["heal"]
            heal_amount = int(parse_value_or_dice(heal_value))
            old_hp = user_entity.hp
            user_entity.heal(heal_amount)
            actual_heal = user_entity.hp - old_hp
            results.append(f"恢复了{actual_heal}点生命值")
        
        # AP恢复 - 支持骰子表达式
        if "restore_ap" in effects:
            ap_value = effects["restore_ap"]
            ap_amount = int(parse_value_or_dice(ap_value))
            old_ap = user_entity.ap
            user_entity.ap = min(user_entity.ap + ap_amount, user_entity.max_ap)
            actual_restore = user_entity.ap - old_ap
            results.append(f"恢复了{actual_restore}点AP")
        
        # 扣除AP（使用物品本身消耗的AP）
        user_entity.ap -= item.ap_cost
        
        if results:
            return True, f"使用了{item.name}：{"、".join(results)}"
        else:
            return False, "物品没有可用效果"
    
    def _equip_item(self, item: InventoryItem, user_entity) -> Tuple[bool, str]:
        """穿戴装备"""
        if not user_entity:
            return False, "没有使用者"
        
        effects = item.use_effects
        
        if "equip_slot" not in effects:
            return False, "物品没有指定装备槽位"
        
        slot = effects["equip_slot"]
        equipment_id = effects.get("equipment_id")
        
        # 这里需要从装备数据库加载装备
        # 暂时返回提示信息
        return False, "装备功能待实现（需要从装备数据库加载）"
    
    def _can_place_at(self, item: InventoryItem, x: int, y: int) -> bool:
        """检查物品是否可以放置在指定位置"""
        positions = self._get_item_positions(item, x, y)
        
        # 检查所有位置是否在网格范围内且未被占用
        for px, py in positions:
            if px < 0 or px >= self.grid_width or py < 0 or py >= self.grid_height:
                return False
            if self.grid[py][px] is not None:
                return False
        
        return True
    
    def _place_item_at(self, item: InventoryItem, x: int, y: int) -> bool:
        """在指定位置放置物品"""
        if not self._can_place_at(item, x, y):
            return False
        
        positions = self._get_item_positions(item, x, y)
        for px, py in positions:
            self.grid[py][px] = item
        
        return True
    
    def _remove_item_from_grid(self, item: InventoryItem):
        """从网格中移除物品"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y][x] == item:
                    self.grid[y][x] = None
    
    def _get_item_positions(self, item: InventoryItem, x: int, y: int) -> List[Tuple[int, int]]:
        """获取物品占据的所有格子位置"""
        positions = [(x, y)]  # 基础位置
        
        if item.shape == ItemShape.HORIZONTAL_2:
            positions.append((x + 1, y))
        elif item.shape == ItemShape.VERTICAL_2:
            positions.append((x, y + 1))
        elif item.shape == ItemShape.SQUARE_2X2:
            positions.extend([
                (x + 1, y),
                (x, y + 1),
                (x + 1, y + 1)
            ])
        elif item.shape == ItemShape.HORIZONTAL_3:
            positions.extend([
                (x + 1, y),
                (x + 2, y)
            ])
        elif item.shape == ItemShape.L_SHAPE:
            positions.extend([
                (x + 1, y),
                (x, y + 1)
            ])
        
        return positions
    
    def _find_placement_position(self, item: InventoryItem) -> Optional[Tuple[int, int]]:
        """自动寻找可以放置物品的位置"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self._can_place_at(item, x, y):
                    return (x, y)
        return None
    
    def __str__(self):
        info = self.get_usage_info()
        return (f"Inventory({self.owner_name}): "
                f"物品数={info['item_count']}, "
                f"体积={info['volume_used']}/{info['volume_max']}, "
                f"重量={info['weight_used']:.1f}/{info['weight_max']:.1f}")

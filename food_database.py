"""
食物物品数据库模块
定义各种食物物品的属性和效果
"""
from inventory import InventoryItem, ItemType, ItemShape
from typing import Dict


def create_food_database() -> Dict[str, InventoryItem]:
    """
    创建食物物品数据库
    
    Returns:
        食物物品字典 {食物名称: InventoryItem}
    """
    foods = {}
    
    # === 基础食物 ===
    
    # 干粮 - 基础口粮，占用1格，可堆叠
    foods["干粮"] = InventoryItem(
        name="干粮",
        item_type=ItemType.CONSUMABLE,
        description="干燥的硬面包和肉干混合物，适合长途旅行携带。\n恢复少量生命值。",
        weight=0.5,
        volume=1,
        shape=ItemShape.SINGLE,
        icon_color=(210, 180, 140),  # 棕褐色
        stackable=True,
        max_stack=10,
        use_effects={"heal": "1d4+1"},  # 恢复1d4+1 HP
        ap_cost=1,
        properties={"food_value": 1, "tags": ["basic", "travel"]}
    )
    
    # 肉干 - 高蛋白食物，占用1格，可堆叠
    foods["肉干"] = InventoryItem(
        name="肉干",
        item_type=ItemType.CONSUMABLE,
        description="风干的兽肉，富含蛋白质。\n恢复中等生命值，提供饱腹感。",
        weight=0.3,
        volume=1,
        shape=ItemShape.SINGLE,
        icon_color=(139, 69, 19),  # 深棕色
        stackable=True,
        max_stack=8,
        use_effects={"heal": "2d4+2"},  # 恢复2d4+2 HP
        ap_cost=1,
        properties={"food_value": 2, "tags": ["meat", "protein"]}
    )
    
    # 新鲜水果 - 轻便可食用，占用1格，可堆叠
    foods["新鲜水果"] = InventoryItem(
        name="新鲜水果",
        item_type=ItemType.CONSUMABLE,
        description="新鲜的苹果或梨子，清脆多汁。\n恢复少量生命值，提供维生素。",
        weight=0.2,
        volume=1,
        shape=ItemShape.SINGLE,
        icon_color=(255, 100, 100),  # 红色
        stackable=True,
        max_stack=6,
        use_effects={"heal": "1d4+2"},  # 恢复1d4+2 HP
        ap_cost=1,
        properties={"food_value": 1, "tags": ["fruit", "fresh"]}
    )
    
    # === 高级食物 ===
    
    # 烤肉 - 美味佳肴，占用2格（横向），不可堆叠
    foods["烤肉"] = InventoryItem(
        name="烤肉",
        item_type=ItemType.CONSUMABLE,
        description="精心烤制的肉类，香气扑鼻。\n恢复大量生命值，提供持久能量。",
        weight=1.5,
        volume=2,
        shape=ItemShape.HORIZONTAL_2,
        icon_color=(205, 133, 63),  # 金棕色
        stackable=False,
        use_effects={"heal": "3d4+3", "restore_ap": 1},  # 恢复3d4+3 HP + 1 AP
        ap_cost=1,
        properties={"food_value": 3, "tags": ["cooked", "delicious"]}
    )
    
    # 炖菜 - 热腾腾的食物，占用2x2格，不可堆叠
    foods["炖菜"] = InventoryItem(
        name="炖菜",
        item_type=ItemType.CONSUMABLE,
        description="用多种食材慢炖而成的热汤，营养丰富。\n恢复大量生命值和AP。",
        weight=2.0,
        volume=4,
        shape=ItemShape.SQUARE_2X2,
        icon_color=(255, 140, 0),  # 橙色
        stackable=False,
        use_effects={"heal": "4d4+4", "restore_ap": 2},  # 恢复4d4+4 HP + 2 AP
        ap_cost=1,
        properties={"food_value": 4, "tags": ["cooked", "hot", "nutritious"]}
    )
    
    # 精灵面包 - 稀有魔法食物，占用1格，不可堆叠
    foods["精灵面包"] = InventoryItem(
        name="精灵面包",
        item_type=ItemType.CONSUMABLE,
        description="传说中精灵族制作的魔法面包，一块就能让人饱足一整天。\n完全恢复生命值和AP。",
        weight=0.1,
        volume=1,
        shape=ItemShape.SINGLE,
        icon_color=(255, 215, 0),  # 金色
        stackable=False,
        use_effects={"heal": "full", "restore_ap": "full"},  # 完全恢复
        ap_cost=1,
        properties={"food_value": 10, "tags": ["magic", "rare", "elven"]}
    )
    
    # === 特殊食物 ===
    
    # 草药茶 - 治疗饮品，占用1格，可堆叠
    foods["草药茶"] = InventoryItem(
        name="草药茶",
        item_type=ItemType.CONSUMABLE,
        description="用多种草药泡制的热茶，有治愈功效。\n恢复生命值并移除一个负面状态。",
        weight=0.3,
        volume=1,
        shape=ItemShape.SINGLE,
        icon_color=(144, 238, 144),  # 浅绿色
        stackable=True,
        max_stack=5,
        use_effects={"heal": "2d4+3", "remove_debuff": 1},  # 恢复2d4+3 HP + 移除1个debuff
        ap_cost=1,
        properties={"food_value": 1, "tags": ["herbal", "healing", "tea"]}
    )
    
    # 能量棒 - 冒险者专用，占用1格，可堆叠
    foods["能量棒"] = InventoryItem(
        name="能量棒",
        item_type=ItemType.CONSUMABLE,
        description="浓缩的能量食品，专为冒险者设计。\n快速恢复AP。",
        weight=0.2,
        volume=1,
        shape=ItemShape.SINGLE,
        icon_color=(255, 165, 0),  # 橙色
        stackable=True,
        max_stack=10,
        use_effects={"restore_ap": 2},  # 恢复2 AP
        ap_cost=0,  # 可以快速食用
        properties={"food_value": 1, "tags": ["energy", "compact"]}
    )
    
    # 蘑菇汤 - 森林特产，占用2格（纵向），不可堆叠
    foods["蘑菇汤"] = InventoryItem(
        name="蘑菇汤",
        item_type=ItemType.CONSUMABLE,
        description="用野生蘑菇熬制的浓汤，味道鲜美。\n恢复生命值并提供临时增益。",
        weight=1.0,
        volume=2,
        shape=ItemShape.VERTICAL_2,
        icon_color=(160, 82, 45),  # 棕色
        stackable=False,
        use_effects={"heal": "3d4+2", "buff_duration": 2},  # 恢复3d4+2 HP + 持续2回合增益
        ap_cost=1,
        properties={"food_value": 2, "tags": ["mushroom", "soup", "forest"]}
    )
    
    # 蜂蜜酒 - 酒精饮料，占用1格，可堆叠
    foods["蜂蜜酒"] = InventoryItem(
        name="蜂蜜酒",
        item_type=ItemType.CONSUMABLE,
        description="甜美的发酵蜂蜜酒，能提振士气。\n恢复少量生命值，提升下一次攻击伤害。",
        weight=0.5,
        volume=1,
        shape=ItemShape.SINGLE,
        icon_color=(255, 215, 0),  # 金黄色
        stackable=True,
        max_stack=4,
        use_effects={"heal": "1d4+1", "damage_bonus": 2},  # 恢复1d4+1 HP + 下次伤害+2
        ap_cost=1,
        properties={"food_value": 1, "tags": ["alcohol", "honey", "boost"]}
    )
    
    return foods


def get_starter_foods() -> list:
    """
    获取初始食物包（玩家开始时拥有的食物）
    
    Returns:
        初始食物列表 [(食物名称, 数量), ...]
    """
    return [
        ("干粮", 5),      # 5份干粮
        ("肉干", 3),      # 3份肉干
        ("新鲜水果", 2),  # 2个水果
        ("能量棒", 3),    # 3根能量棒
    ]


if __name__ == "__main__":
    # 测试食物数据库
    foods_db = create_food_database()
    
    print("=" * 70)
    print("食物物品数据库")
    print("=" * 70)
    
    for name, food in foods_db.items():
        print(f"\n{name}:")
        print(f"  描述: {food.description}")
        print(f"  重量: {food.weight}")
        print(f"  体积: {food.volume} 格")
        print(f"  形状: {food.shape.value}")
        print(f"  可堆叠: {'是' if food.stackable else '否'}")
        if food.stackable:
            print(f"  最大堆叠: {food.max_stack}")
        print(f"  使用效果: {food.use_effects}")
        print(f"  AP消耗: {food.ap_cost}")
    
    print("\n" + "=" * 70)
    print(f"总计: {len(foods_db)} 种食物")
    print("=" * 70)
    
    # 测试初始食物包
    print("\n初始食物包:")
    for food_name, count in get_starter_foods():
        print(f"  {food_name} x{count}")

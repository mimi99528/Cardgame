"""
卡牌序列化高级用法示例
演示如何处理复杂的打出条件和效果
"""
from models import Card
from config import CardType, Rarity
from card_serializer import (
    CardSerializer,
    ConditionEffectSerializer,
    serialize_cards_to_json,
    deserialize_cards_from_json
)


def create_advanced_card():
    """创建具有复杂条件和效果的高级卡牌"""
    
    # 定义打出条件列表
    play_conditions = [
        {
            "type": "min_ap",
            "value": 3,
            "description": "需要至少3点AP"
        },
        {
            "type": "enemy_hp_below",
            "value": 50,
            "description": "敌人生命值低于50%"
        },
        {
            "type": "has_buff",
            "buff_type": "pot",
            "description": "目标必须有中毒效果"
        }
    ]
    
    # 定义效果列表（结构化格式）
    effects_list = [
        {
            "type": "damage",
            "value": 40,
            "target": "enemy",
            "damage_type": "physical",
            "description": "对敌人造成40点物理伤害"
        },
        {
            "type": "apply_debuff",
            "buff_type": "pot",
            "stacks": 3,
            "duration": 3,
            "target": "enemy",
            "description": "施加3层中毒，持续3回合"
        },
        {
            "type": "self_heal",
            "value": 15,
            "target": "self",
            "description": "恢复15点生命值"
        }
    ]
    
    # 创建卡牌（使用传统的effects字典）
    card = Card(
        name="致命连击",
        card_type=CardType.ATTACK_PHYSICAL,
        ap_cost=3,
        effects={
            "hp": -40,
            "pot_3": 3
        },
        description="强力的连续攻击，造成伤害并施加中毒",
        rarity=Rarity.RARE
    )
    
    # 将条件和效果添加到卡牌对象（作为扩展属性）
    card.play_conditions = play_conditions
    card.effects_list = effects_list
    
    return card


def test_advanced_serialization():
    """测试高级卡牌的序列化"""
    print("=" * 60)
    print("高级卡牌序列化示例")
    print("=" * 60)
    
    # 创建高级卡牌
    advanced_card = create_advanced_card()
    
    print(f"\n原始卡牌: {advanced_card}")
    print(f"  - 名称: {advanced_card.name}")
    print(f"  - 类型: {advanced_card.card_type}")
    print(f"  - AP消耗: {advanced_card.ap_cost}")
    print(f"  - 稀有度: {advanced_card.rarity}")
    
    # 显示打出条件
    print(f"\n  打出条件 ({len(advanced_card.play_conditions)}个):")
    for i, condition in enumerate(advanced_card.play_conditions, 1):
        print(f"    {i}. [{condition['type']}] {condition['description']}")
    
    # 显示效果列表
    print(f"\n  效果列表 ({len(advanced_card.effects_list)}个):")
    for i, effect in enumerate(advanced_card.effects_list, 1):
        print(f"    {i}. [{effect['type']}] {effect['description']}")
    
    # 序列化条件列表
    conditions_serialized = ConditionEffectSerializer.conditions_list_to_dict(
        advanced_card.play_conditions
    )
    
    # 序列化效果列表
    effects_serialized = ConditionEffectSerializer.effects_list_to_dict(
        advanced_card.effects_list
    )
    
    print(f"\n✓ 条件和效果序列化成功")
    print(f"  - 条件数量: {len(conditions_serialized)}")
    print(f"  - 效果数量: {len(effects_serialized)}")
    
    return True


def demonstrate_json_structure():
    """演示完整的JSON结构"""
    print("\n" + "=" * 60)
    print("完整JSON结构示例")
    print("=" * 60)
    
    from card_database import create_card_database
    
    cards_db = create_card_database()
    
    # 选择几张卡牌
    sample_cards = [
        cards_db["basic_attack"],
        cards_db["fireball"],
        cards_db["heal"]
    ]
    
    # 序列化为JSON
    json_str = serialize_cards_to_json(sample_cards)
    
    print("\n生成的JSON格式:")
    print(json_str)
    
    print("\n\n关键字段说明:")
    print("  - id: 卡牌唯一标识符（整数）")
    print("  - name: 卡牌名称（字符串）")
    print("  - type: 卡牌类型（字符串枚举值）")
    print("  - description: 卡牌描述（字符串）")
    print("  - rarity: 稀有度（字符串枚举名）")
    print("  - ap_cost: AP消耗（整数）")
    print("  - effects: 效果字典（键值对）")
    print("  - play_conditions: 打出条件列表（预留字段）")
    print("  - card_category: 卡牌分类（预留字段，如'combat'）")
    
    return True


def show_usage_examples():
    """展示使用示例"""
    print("\n" + "=" * 60)
    print("使用示例")
    print("=" * 60)
    
    print("""
1. 序列化单个卡牌为字典:
   from card_serializer import serialize_card
   card_dict = serialize_card(my_card)

2. 从字典反序列化卡牌:
   from card_serializer import deserialize_card
   restored_card = deserialize_card(card_dict)

3. 序列化卡牌列表为JSON字符串:
   from card_serializer import serialize_cards_to_json
   json_str = serialize_cards_to_json(cards_list)

4. 从JSON字符串加载卡牌列表:
   from card_serializer import deserialize_cards_from_json
   cards = deserialize_cards_from_json(json_str)

5. 保存到文件:
   from card_serializer import CardSerializer
   CardSerializer.save_cards_to_file(cards, 'cards.json')

6. 从文件加载:
   loaded_cards = CardSerializer.load_cards_from_file('cards.json')

7. 序列化复杂条件:
   from card_serializer import ConditionEffectSerializer
   conditions_dict = ConditionEffectSerializer.conditions_list_to_dict(conditions)
   effects_dict = ConditionEffectSerializer.effects_list_to_dict(effects)
    """)
    
    return True


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("卡牌序列化高级用法")
    print("=" * 60)
    
    try:
        test_advanced_serialization()
        demonstrate_json_structure()
        show_usage_examples()
        
        print("\n" + "=" * 60)
        print("所有示例执行完成! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

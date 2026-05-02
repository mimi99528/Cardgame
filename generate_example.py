"""
生成示例JSON文件，展示新的结构化格式
"""
import json
from card_database import create_card_database
from card_serializer import CardSerializer, ConditionEffectSerializer


def generate_example_json():
    """生成示例JSON文件"""
    
    cards_db = create_card_database()
    
    # 选择几张卡牌
    example_cards = [
        cards_db["basic_attack"],
        cards_db["serious_strike"],
        cards_db["fireball"],
        cards_db["heal"],
        cards_db["shield"],
        cards_db["poison"],
    ]
    
    # 序列化为JSON（从ID=1开始）
    json_str = CardSerializer.cards_to_json(example_cards, start_id=1, indent=2)
    
    # 保存到文件
    with open('example_structured_cards.json', 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    print("✓ 已生成示例文件: example_structured_cards.json")
    print(f"\n包含 {len(example_cards)} 张卡牌")
    print("\nJSON结构预览:")
    print(json_str[:500])


def demonstrate_advanced_usage():
    """演示高级用法：手动创建带条件和效果的卡牌"""
    
    print("\n" + "=" * 60)
    print("高级用法演示")
    print("=" * 60)
    
    # 创建一个复杂的效果列表
    effects = [
        ConditionEffectSerializer.create_effect("emy_dmg", amount=30),
        ConditionEffectSerializer.create_effect("emy_debuff", buff_type="pot", stacks=2, duration=3),
        ConditionEffectSerializer.create_effect("self_heal", amount=10),
    ]
    
    # 创建一个复杂的条件列表
    conditions = [
        ConditionEffectSerializer.create_condition("min_ap", value=3),
        ConditionEffectSerializer.create_condition("enemy_hp_below", percentage=60),
    ]
    
    # 构建卡牌字典
    advanced_card = {
        "id": 100,
        "name": "毒刃突袭",
        "category": "combat",
        "type": "atk_phy",
        "description": "造成30点伤害，施加2层中毒并恢复10点生命",
        "rarity": "RARE",
        "ap_cost": 3,
        "effects": effects,
        "play_conditions": conditions
    }
    
    print("\n高级卡牌示例:")
    print(json.dumps(advanced_card, indent=2, ensure_ascii=False))
    
    # 保存为单独的文件
    with open('example_advanced_card.json', 'w', encoding='utf-8') as f:
        json.dump(advanced_card, f, indent=2, ensure_ascii=False)
    
    print("\n✓ 已生成高级示例文件: example_advanced_card.json")


def main():
    """主函数"""
    print("=" * 60)
    print("生成结构化格式示例")
    print("=" * 60)
    
    generate_example_json()
    demonstrate_advanced_usage()
    
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

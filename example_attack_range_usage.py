"""
攻击距离和范围使用示例
演示如何创建和使用具有不同攻击范围的卡牌
"""
from models import Card, Entity
from config import CardType, Rarity
from card_serializer import CardSerializer


def create_example_cards():
    """创建示例卡牌"""
    
    # 1. 近战攻击 - 剑士的基本攻击
    sword_slash = Card(
        name="剑刃斩击",
        card_type=CardType.ATTACK_PHYSICAL,
        ap_cost=1,
        effects={"hp": -12},
        description="使用剑刃进行近战攻击",
        rarity=Rarity.COMMON,
        atk_dis=1,  # 近战
        atk_rnge={"type": "circle", "radius": 1}  # 只能攻击相邻目标
    )
    
    # 2. 中程攻击 - 长矛突刺
    spear_thrust = Card(
        name="长矛突刺",
        card_type=CardType.ATTACK_PHYSICAL,
        ap_cost=2,
        effects={"hp": -18},
        description="使用长矛进行中距离直线攻击",
        rarity=Rarity.UNCOMMON,
        atk_dis=2,  # 中距离
        atk_rnge={"type": "line", "length": 3, "width": 1}  # 直线范围
    )
    
    # 3. 远程攻击 - 弓箭射击
    arrow_shot = Card(
        name="精准射击",
        card_type=CardType.ATTACK_PHYSICAL,
        ap_cost=1,
        effects={"hp": -15},
        description="远程弓箭精准射击",
        rarity=Rarity.COMMON,
        atk_dis=4,  # 远程
        atk_rnge={"type": "circle", "radius": 1}  # 单体目标
    )
    
    # 4. 范围魔法 - 火球术
    fireball = Card(
        name="火球术",
        card_type=CardType.ATTACK_MAGICAL,
        ap_cost=3,
        effects={"hp": -20},
        description="发射火球造成范围爆炸伤害",
        rarity=Rarity.RARE,
        atk_dis=5,  # 远程施法
        atk_rnge={"type": "circle", "radius": 2}  # 半径2的圆形范围
    )
    
    # 5. 连锁攻击 - 闪电链
    chain_lightning = Card(
        name="闪电链",
        card_type=CardType.ATTACK_MAGICAL,
        ap_cost=4,
        effects={"hp": -15},
        description="连锁闪电攻击多个敌人",
        rarity=Rarity.LEGENDARY,
        atk_dis=6,  # 超远程
        atk_rnge={
            "type": "chain",
            "max_targets": 3,
            "max_distance": 4
        }  # 最多连锁3个目标
    )
    
    # 6. 大范围攻击 - 地震术
    earthquake = Card(
        name="地震术",
        card_type=CardType.ATTACK_MAGICAL,
        ap_cost=5,
        effects={"hp": -25},
        description="引发地震造成大范围伤害",
        rarity=Rarity.LEGENDARY,
        atk_dis=3,  # 中距离施法
        atk_rnge={"type": "circle", "radius": 3}  # 半径3的大范围
    )
    
    # 7. 自我治疗
    self_heal = Card(
        name="自我治疗",
        card_type=CardType.HEAL,
        ap_cost=2,
        effects={"hp": 25},
        description="恢复自身生命值",
        rarity=Rarity.COMMON,
        atk_dis=0,  # 自身
        atk_rnge={"type": "self", "radius": 0}  # 只影响自己
    )
    
    # 8. 群体治疗
    group_heal = Card(
        name="群体治疗",
        card_type=CardType.HEAL,
        ap_cost=4,
        effects={"hp": 15},
        description="治疗周围友方单位",
        rarity=Rarity.RARE,
        atk_dis=0,  # 以自身为中心
        atk_rnge={"type": "circle", "radius": 2}  # 半径2范围内的友方
    )
    
    # 9. 锥形攻击 - 龙息
    dragon_breath = Card(
        name="龙息",
        card_type=CardType.ATTACK_MAGICAL,
        ap_cost=4,
        effects={"hp": -22},
        description="喷吐火焰锥形攻击",
        rarity=Rarity.LEGENDARY,
        atk_dis=2,
        atk_rnge={"type": "cone", "angle": 90, "distance": 4}  # 90度锥形
    )
    
    # 10. Debuff范围 - 毒雾
    poison_cloud = Card(
        name="毒雾",
        card_type=CardType.BUFF,
        ap_cost=3,
        effects={"pot_2": 2},
        description="在区域内释放毒雾",
        rarity=Rarity.RARE,
        atk_dis=3,
        atk_rnge={"type": "circle", "radius": 2}  # 半径2的毒雾区域
    )
    
    return [
        sword_slash, spear_thrust, arrow_shot, fireball,
        chain_lightning, earthquake, self_heal, group_heal,
        dragon_breath, poison_cloud
    ]


def display_card_info(cards):
    """显示卡牌信息"""
    
    print("=" * 70)
    print("攻击距离和范围示例卡牌")
    print("=" * 70)
    print()
    
    for i, card in enumerate(cards, 1):
        print(f"{i}. {card.name}")
        print(f"   类型: {card.card_type.value}")
        print(f"   AP消耗: {card.ap_cost}")
        print(f"   稀有度: {card.rarity.name}")
        print(f"   描述: {card.description}")
        print(f"   攻击距离: {card.atk_dis}")
        print(f"   攻击范围: {card.atk_rnge}")
        
        # 解释攻击范围
        range_type = card.atk_rnge.get("type", "unknown")
        if range_type == "self":
            print(f"   → 范围说明: 仅对自身生效")
        elif range_type == "circle":
            radius = card.atk_rnge.get("radius", 0)
            print(f"   → 范围说明: 半径为{radius}的圆形区域")
        elif range_type == "line":
            length = card.atk_rnge.get("length", 0)
            width = card.atk_rnge.get("width", 0)
            print(f"   → 范围说明: {length}x{width}的直线区域")
        elif range_type == "cone":
            angle = card.atk_rnge.get("angle", 0)
            distance = card.atk_rnge.get("distance", 0)
            print(f"   → 范围说明: {angle}度锥形，最远{distance}格")
        elif range_type == "chain":
            max_targets = card.atk_rnge.get("max_targets", 0)
            max_distance = card.atk_rnge.get("max_distance", 0)
            print(f"   → 范围说明: 最多连锁{max_targets}个目标，间距{max_distance}格")
        
        print()


def save_and_load_example(cards):
    """演示保存和加载"""
    
    print("=" * 70)
    print("序列化示例")
    print("=" * 70)
    print()
    
    # 保存到JSON文件
    filename = "example_attack_range_cards.json"
    CardSerializer.save_cards_to_file(cards, filename)
    print(f"✓ 已将 {len(cards)} 张卡牌保存到 {filename}")
    print()
    
    # 从JSON文件加载
    loaded_cards = CardSerializer.load_cards_from_file(filename)
    print(f"✓ 已从 {filename} 加载 {len(loaded_cards)} 张卡牌")
    print()
    
    # 验证数据完整性
    print("验证加载的卡牌数据:")
    for original, loaded in zip(cards, loaded_cards):
        match = (
            original.atk_dis == loaded.atk_dis and
            original.atk_rnge == loaded.atk_rnge
        )
        status = "✓" if match else "✗"
        print(f"  {status} {loaded.name}: 攻击距离={loaded.atk_dis}, "
              f"范围类型={loaded.atk_rnge['type']}")
    
    print()


def main():
    """主函数"""
    
    # 创建示例卡牌
    cards = create_example_cards()
    
    # 显示卡牌信息
    display_card_info(cards)
    
    # 演示序列化和反序列化
    save_and_load_example(cards)
    
    print("=" * 70)
    print("示例完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
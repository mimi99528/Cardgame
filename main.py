"""
卡牌战斗游戏 - 主程序入口
使用 Arcade 引擎重构版本
"""
import arcade
from battle_system import BattleSystem
from card_database import create_player_character, create_enemy, create_ally_ai, create_enemy_2
from game_view import CardView
from config import CONSTANTS
from tile_map import TileMap
from career_system import CareerFactory
from careers.farmer_passive import setup_farmer_passives
from careers.scholar_passive import setup_scholar_passives
from character_creation import CharacterCreationView


def demo_serialization():
    """演示卡牌序列化功能"""
    print("\n" + "=" * 60)
    print("卡牌序列化功能演示")
    print("=" * 60)
    
    from card_database import create_card_database
    from card_serializer import CardSerializer, serialize_cards_to_json
    
    # 创建卡牌数据库
    cards_db = create_card_database()
    
    if not cards_db:
        print("警告：卡牌数据库为空，跳过序列化演示")
        return
    
    # 选择几张卡牌进行演示（使用JSON中的卡牌名称）
    demo_cards = []
    for card_name in ["刺击", "劈砍", "治疗", "格挡"]:
        if card_name in cards_db:
            demo_cards.append(cards_db[card_name])
    
    if not demo_cards:
        print("警告：没有找到可用的卡牌，跳过序列化演示")
        return
    
    print(f"\n选择了 {len(demo_cards)} 张卡牌进行序列化演示:")
    for card in demo_cards:
        print(f"  - {card.name}")
    
    # 序列化为JSON
    json_str = serialize_cards_to_json(demo_cards)
    print(f"\n✓ 序列化成功，JSON长度: {len(json_str)} 字符")
    
    # 保存到文件
    filepath = "test_cards.json"
    CardSerializer.save_cards_to_file(demo_cards, filepath)
    print(f"✓ 已保存到文件: {filepath}")
    
    # 从文件加载
    loaded_cards = CardSerializer.load_cards_from_file(filepath)
    print(f"✓ 从文件加载成功，共 {len(loaded_cards)} 张卡牌")
    
    # 验证数据一致性
    all_match = True
    for orig, loaded in zip(demo_cards, loaded_cards):
        if (orig.name != loaded.name or 
            orig.card_type != loaded.card_type or
            orig.ap_cost != loaded.ap_cost):
            all_match = False
            break
    
    if all_match:
        print("✓ 数据验证通过，所有卡牌信息一致")
    else:
        print("✗ 数据验证失败")
    
    print("=" * 60)


class CardGame(arcade.Window):
    """卡牌战斗游戏主窗口"""
    
    def __init__(self):
        # 获取真实屏幕分辨率
        screen_width, screen_height = arcade.get_display_size()
        if not screen_width or not screen_height:
            screen_width = CONSTANTS.WINDOW_WIDTH
            screen_height = CONSTANTS.WINDOW_HEIGHT
        
        super().__init__(
            screen_width,
            screen_height,
            CONSTANTS.WINDOW_TITLE,
            fullscreen=True  # 全屏模式
        )
        
        # 设置背景色为白色（与原版一致）
        arcade.set_background_color(arcade.color.WHITE)
        
        # 初始化游戏
        self.setup_game()
    
    def setup_game(self):
        """设置游戏 - 先显示角色创建界面"""
        # 创建角色创建视图
        character_creation_view = CharacterCreationView(self.on_character_created)
        self.show_view(character_creation_view)
    
    def on_character_created(self, player):
        """角色创建完成回调"""
        print(f"✓ 角色创建完成: {player.name}")
        print(f"  职业: {player.career.name if player.career else '无'}")
        print(f"  属性: 力量{player.stats.strength}, 敏捷{player.stats.dexterity}, "
              f"心智{player.stats.intelligence}, 魅力{player.stats.charisma}")
        
        # 创建敌人（使用不同的敌人类型）
        enemy = create_enemy(enemy_type="warrior")  # 战士型敌人
        enemy_2 = create_enemy_2(enemy_type="mage")  # 法师型敌人
        
        # 创建额外的队友（可选，使用不同职业）
        ally_ai = create_ally_ai()  # 默认均衡型队友
        
        # 创建战斗系统
        battle = BattleSystem(
            player_team=[player, ally_ai],
            enemy_team=[enemy, enemy_2]
        )
        
        # 开始战斗
        battle.start_battle()
        
        # 创建并显示游戏视图
        game_view = CardView(battle)
        self.show_view(game_view)


def main():
    """主函数"""
    print("=" * 60)
    print("卡牌战斗游戏 - Arcade 重构版")
    print("=" * 60)
    print("\n游戏说明：")
    print("- 点击手牌中的卡牌来使用它们")
    print("- 空格键：跳过当前回合")
    print("- ESC键：退出游戏（战斗结束后）")
    print("- 鼠标悬停在卡牌上查看详细信息")
    print("\n" + "=" * 60)
    
    # 初始化职业系统
    CareerFactory.initialize()
    
    # 初始化所有职业被动效果
    from careers.artisan_passive import setup_artisan_passives
    from careers.drifter_passive import setup_drifter_passives
    from careers.pedlar_passive import setup_pedlar_passives
    
    setup_artisan_passives()
    setup_drifter_passives()
    setup_pedlar_passives()
    setup_farmer_passives()
    setup_scholar_passives()
    
    print("✓ 职业系统和被动效果已初始化")
    
    # 演示卡牌序列化功能
    demo_serialization()
    
    # 创建游戏窗口
    game = CardGame()
    
    # 运行游戏
    arcade.run()


if __name__ == "__main__":
    main()

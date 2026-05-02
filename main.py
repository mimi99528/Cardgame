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


def demo_serialization():
    """演示卡牌序列化功能"""
    print("\n" + "=" * 60)
    print("卡牌序列化功能演示")
    print("=" * 60)
    
    from card_database import create_card_database
    from card_serializer import CardSerializer, serialize_cards_to_json
    
    # 创建卡牌数据库
    cards_db = create_card_database()
    
    # 选择几张卡牌进行演示
    demo_cards = [
        cards_db["basic_attack"],
        cards_db["fireball"],
        cards_db["heal"],
        cards_db["shield"]
    ]
    
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
        """设置游戏"""
        # 创建玩家和敌人
        player = create_player_character()
        enemy = create_enemy()
        
        # 创建额外的队友和敌人（可选）
        ally_ai = create_ally_ai()
        enemy_2 = create_enemy_2()
        
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
    
    # 演示卡牌序列化功能
    demo_serialization()
    
    # 创建游戏窗口
    game = CardGame()
    
    # 运行游戏
    arcade.run()


if __name__ == "__main__":
    main()

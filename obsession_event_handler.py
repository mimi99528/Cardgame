"""
执念事件处理器模块
负责处理与执念系统相关的各种游戏事件
"""
from event_system import (
    GameEventType, 
    register_event_handler, 
    trigger_event,
    GameEvent
)
from obsession_system import ObsessionType
from models import Entity


class ObsessionEventHandler:
    """执念事件处理器 - 管理所有执念相关的事件监听和处理"""
    
    @staticmethod
    def setup_obsession_event_handlers():
        """设置执念相关的事件处理器"""
        
        # 注册战斗胜利事件处理器（用于力量、复仇等执念）
        register_event_handler(
            GameEventType.BATTLE_VICTORY,
            ObsessionEventHandler.on_battle_victory,
            priority=50
        )
        
        # 注册击败特定敌人事件处理器（用于复仇、守护等执念）
        register_event_handler(
            GameEventType.ENEMY_DEFEATED,
            ObsessionEventHandler.on_enemy_defeated,
            priority=60
        )
        
        # 注册访问地点事件处理器（用于求知、真相等执念）
        register_event_handler(
            GameEventType.LOCATION_VISITED,
            ObsessionEventHandler.on_location_visited,
            priority=50
        )
        
        # 注册收集物品事件处理器（用于求知、财富等执念）
        register_event_handler(
            GameEventType.ITEM_COLLECTED,
            ObsessionEventHandler.on_item_collected,
            priority=50
        )
        
        # 注册社交检定事件处理器（用于救赎、自由等执念）
        register_event_handler(
            GameEventType.SOCIAL_CHECK_COMPLETED,
            ObsessionEventHandler.on_social_check_completed,
            priority=50
        )
        
        # 注册心智检定事件处理器（用于求知、真相等执念）
        register_event_handler(
            GameEventType.INTELLECT_CHECK_COMPLETED,
            ObsessionEventHandler.on_intellect_check_completed,
            priority=50
        )
        
        # 注册守护行为事件处理器（用于守护执念）
        register_event_handler(
            GameEventType.PROTECTION_ACTION,
            ObsessionEventHandler.on_protection_action,
            priority=50
        )
        
        # 注册帮助NPC事件处理器（用于救赎执念）
        register_event_handler(
            GameEventType.NPC_HELPED,
            ObsessionEventHandler.on_npc_helped,
            priority=50
        )
        
        # 注册任务完成事件处理器（用于救赎、力量等执念）
        register_event_handler(
            GameEventType.QUEST_COMPLETED,
            ObsessionEventHandler.on_quest_completed,
            priority=50
        )
        
        # 注册等级提升事件处理器（用于力量执念）
        register_event_handler(
            GameEventType.LEVEL_UP,
            ObsessionEventHandler.on_level_up,
            priority=50
        )
        
        print("[执念事件] 执念事件处理器已设置完成")
    
    @staticmethod
    def on_battle_victory(event: GameEvent):
        """战斗胜利事件处理"""
        player = event.target
        if not isinstance(player, Entity) or not player.obsession:
            return
        
        # 更新力量执念的战斗胜利进度
        if player.obsession.obsession_type == ObsessionType.POWER:
            old_progress = player.obsession.get_progress_percentage()
            player.obsession.update_condition_progress("win_battle", "difficult_battle", 1)
            new_progress = player.obsession.get_progress_percentage()
            print(f"[执念事件] 战斗胜利 - {player.obsession.name} 进度更新")
            
            # 触发UI提示（如果当前在地图视图）
            self._trigger_map_notification(player, old_progress, new_progress)
            
            # 检查是否完成
            if player.obsession.check_all_conditions():
                player.obsession.is_completed = True
                print(f"[执念事件] ✨ 执念「{player.obsession.name}」已完成！")
    
    @staticmethod
    def _trigger_map_notification(player: Entity, old_progress: float, new_progress: float):
        """
        触发地图视图的执念进度通知
        
        Args:
            player: 玩家实体
            old_progress: 旧进度
            new_progress: 新进度
        """
        try:
            from arcade import get_window
            window = get_window()
            if window and hasattr(window, 'current_view'):
                current_view = window.current_view
                # 检查当前视图是否是 MapView 或其子类
                if hasattr(current_view, 'show_obsession_progress_change'):
                    is_completed = player.obsession.check_all_conditions()
                    current_view.show_obsession_progress_change(
                        old_progress, 
                        new_progress, 
                        player.obsession.name,
                        is_completed
                    )
        except Exception as e:
            print(f"[执念事件] 触发UI通知失败: {e}")

    @staticmethod
    def on_enemy_defeated(event: GameEvent):
        """击败敌人事件处理"""
        player = event.target
        enemy_id = event.get_value("enemy_id", "")
        
        if not isinstance(player, Entity) or not player.obsession or not enemy_id:
            return
        
        # 更新复仇执念的击败敌人进度
        if player.obsession.obsession_type == ObsessionType.REVENGE:
            old_progress = player.obsession.get_progress_percentage()
            player.obsession.update_condition_progress("defeat_enemy", enemy_id, 1)
            new_progress = player.obsession.get_progress_percentage()
            print(f"[执念事件] 击败敌人 {enemy_id} - {player.obsession.name} 进度更新")
            self._trigger_map_notification(player, old_progress, new_progress)
        
        # 更新守护执念的击败入侵者进度
        elif player.obsession.obsession_type == ObsessionType.PROTECTION:
            if "invader" in enemy_id.lower() or "attacker" in enemy_id.lower():
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("defeat_enemy", "temple_invader", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 击败入侵者 {enemy_id} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 更新力量执念的击败Boss进度
        elif player.obsession.obsession_type == ObsessionType.POWER:
            if "boss" in enemy_id.lower() or "elite" in enemy_id.lower():
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("defeat_enemy", "boss_enemy", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 击败Boss {enemy_id} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 检查是否完成
        if player.obsession.check_all_conditions():
            player.obsession.is_completed = True
            print(f"[执念事件] ✨ 执念「{player.obsession.name}」已完成！")
    
    @staticmethod
    def on_location_visited(event: GameEvent):
        """访问地点事件处理"""
        player = event.target
        location_id = event.get_value("location_id", "")
        
        if not isinstance(player, Entity) or not player.obsession or not location_id:
            return
        
        # 更新求知执念的探索遗迹进度
        if player.obsession.obsession_type == ObsessionType.KNOWLEDGE:
            if "ruins" in location_id.lower() or "ancient" in location_id.lower():
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("visit_location", "ancient_ruins", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 访问古代遗迹 {location_id} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 更新守护执念的守护圣地进度
        elif player.obsession.obsession_type == ObsessionType.PROTECTION:
            if "temple" in location_id.lower() or "sacred" in location_id.lower():
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("defend_location", "sacred_temple", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 守护圣地 {location_id} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 更新真相执念的访问祭坛进度
        elif player.obsession.obsession_type == ObsessionType.TRUTH:
            if "altar" in location_id.lower():
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("visit_location", "altar_site", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 访问祭坛 {location_id} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 检查是否完成
        if player.obsession.check_all_conditions():
            player.obsession.is_completed = True
            print(f"[执念事件] ✨ 执念「{player.obsession.name}」已完成！")
    
    @staticmethod
    def on_item_collected(event: GameEvent):
        """收集物品事件处理"""
        player = event.target
        item_id = event.get_value("item_id", "")
        
        if not isinstance(player, Entity) or not player.obsession or not item_id:
            return
        
        # 更新求知执念的收集典籍进度
        if player.obsession.obsession_type == ObsessionType.KNOWLEDGE:
            if "tome" in item_id.lower() or "book" in item_id.lower() or "scroll" in item_id.lower():
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("collect_item", "ancient_tome", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 收集典籍 {item_id} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 检查是否完成
        if player.obsession.check_all_conditions():
            player.obsession.is_completed = True
            print(f"[执念事件] ✨ 执念「{player.obsession.name}」已完成！")
    
    @staticmethod
    def on_social_check_completed(event: GameEvent):
        """社交检定完成事件处理"""
        player = event.target
        check_result = event.get_value("check_result", "")
        
        if not isinstance(player, Entity) or not player.obsession:
            return
        
        # 如果社交检定成功，可以更新某些执念进度
        if check_result in ["大成功", "成功"]:
            # 这里可以根据具体情况更新不同的执念
            print(f"[执念事件] 社交检定{check_result} - {player.obsession.name} 可能获得进度")
    
    @staticmethod
    def on_intellect_check_completed(event: GameEvent):
        """心智检定完成事件处理"""
        player = event.target
        check_result = event.get_value("check_result", "")
        
        if not isinstance(player, Entity) or not player.obsession:
            return
        
        # 更新求知执念的心智检定进度
        if player.obsession.obsession_type == ObsessionType.KNOWLEDGE:
            if check_result in ["大成功", "成功"]:
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("complete_check", "intelligence_check_hard", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 心智检定{check_result} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 更新真相执念的祭坛检定进度
        elif player.obsession.obsession_type == ObsessionType.TRUTH:
            if check_result in ["大成功", "成功"]:
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("complete_check", "altar_intelligence_check", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 祭坛心智检定{check_result} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 检查是否完成
        if player.obsession.check_all_conditions():
            player.obsession.is_completed = True
            print(f"[执念事件] ✨ 执念「{player.obsession.name}」已完成！")
    
    @staticmethod
    def on_protection_action(event: GameEvent):
        """守护行为事件处理"""
        player = event.target
        
        if not isinstance(player, Entity) or not player.obsession:
            return
        
        # 更新守护执念的守护进度
        if player.obsession.obsession_type == ObsessionType.PROTECTION:
            old_progress = player.obsession.get_progress_percentage()
            player.obsession.update_condition_progress("defend_location", "sacred_temple", 1)
            new_progress = player.obsession.get_progress_percentage()
            print(f"[执念事件] 守护行为 - {player.obsession.name} 进度更新")
            self._trigger_map_notification(player, old_progress, new_progress)
        
        # 检查是否完成
        if player.obsession.check_all_conditions():
            player.obsession.is_completed = True
            print(f"[执念事件] ✨ 执念「{player.obsession.name}」已完成！")
    
    @staticmethod
    def on_npc_helped(event: GameEvent):
        """帮助NPC事件处理"""
        player = event.target
        npc_count = event.get_value("npc_count", 1)
        
        if not isinstance(player, Entity) or not player.obsession:
            return
        
        # 更新救赎执念的帮助村民进度
        if player.obsession.obsession_type == ObsessionType.REDEMPTION:
            old_progress = player.obsession.get_progress_percentage()
            player.obsession.update_condition_progress("help_npc", "villager", npc_count)
            new_progress = player.obsession.get_progress_percentage()
            print(f"[执念事件] 帮助NPC x{npc_count} - {player.obsession.name} 进度更新")
            self._trigger_map_notification(player, old_progress, new_progress)
        
        # 检查是否完成
        if player.obsession.check_all_conditions():
            player.obsession.is_completed = True
            print(f"[执念事件] ✨ 执念「{player.obsession.name}」已完成！")
    
    @staticmethod
    def on_quest_completed(event: GameEvent):
        """任务完成事件处理"""
        player = event.target
        quest_id = event.get_value("quest_id", "")
        
        if not isinstance(player, Entity) or not player.obsession:
            return
        
        # 更新救赎执念的救援任务进度
        if player.obsession.obsession_type == ObsessionType.REDEMPTION:
            if "rescue" in quest_id.lower() or "mission" in quest_id.lower():
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("complete_quest", "rescue_mission", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 完成任务 {quest_id} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 检查是否完成
        if player.obsession.check_all_conditions():
            player.obsession.is_completed = True
            print(f"[执念事件] ✨ 执念「{player.obsession.name}」已完成！")
    
    @staticmethod
    def on_level_up(event: GameEvent):
        """等级提升事件处理"""
        player = event.target
        new_level = event.get_value("new_level", 1)
        
        if not isinstance(player, Entity) or not player.obsession:
            return
        
        # 更新力量执念的等级进度
        if player.obsession.obsession_type == ObsessionType.POWER:
            if new_level >= 10:
                old_progress = player.obsession.get_progress_percentage()
                player.obsession.update_condition_progress("reach_level", "level_10", 1)
                new_progress = player.obsession.get_progress_percentage()
                print(f"[执念事件] 达到等级 {new_level} - {player.obsession.name} 进度更新")
                self._trigger_map_notification(player, old_progress, new_progress)
        
        # 检查是否完成
        if player.obsession.check_all_conditions():
            player.obsession.is_completed = True
            print(f"[执念事件] ✨ 执念「{player.obsession.name}」已完成！")


# 便捷函数
def setup_obsession_events():
    """设置所有执念相关事件处理器"""
    ObsessionEventHandler.setup_obsession_event_handlers()


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("执念事件处理器测试")
    print("=" * 60)
    
    # 设置执念事件处理器
    setup_obsession_events()
    
    print("\n✓ 执念事件处理器已设置")
    print("=" * 60)

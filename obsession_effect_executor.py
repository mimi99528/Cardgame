"""
执念效果执行器模块
负责在叙事结果中执行执念相关的效果
"""
from typing import Any, Dict, List
from models import Entity


class ObsessionEffectExecutor:
    """执念效果执行器"""
    
    @staticmethod
    def execute_effect(effect: Dict[str, Any], player: Entity, battle_log=None) -> List[str]:
        """
        执行执念相关效果
        
        Args:
            effect: 效果字典
            player: 玩家实体
            battle_log: 战斗日志（可选）
            
        Returns:
            效果描述列表
        """
        results = []
        effect_type = effect.get("type", "")
        
        if effect_type == "update_obsession_progress":
            results.extend(ObsessionEffectExecutor._update_obsession_progress(effect, player))
        elif effect_type == "check_obsession_completion":
            results.extend(ObsessionEffectExecutor._check_obsession_completion(player))
        
        return results
    
    @staticmethod
    def _update_obsession_progress(effect: Dict[str, Any], player: Entity) -> List[str]:
        """
        更新执念进度
        
        Args:
            effect: 效果字典，包含 condition_type, target_id, amount
            player: 玩家实体
            
        Returns:
            效果描述列表
        """
        results = []
        
        if not player.obsession:
            results.append("[执念] 角色没有执念，无法更新进度")
            return results
        
        condition_type = effect.get("condition_type", "")
        target_id = effect.get("target_id", "")
        amount = effect.get("amount", 1)
        
        if not condition_type or not target_id:
            results.append("[执念] 效果参数不完整")
            return results
        
        # 更新执念条件进度
        old_progress = player.obsession.get_progress_percentage()
        player.obsession.update_condition_progress(condition_type, target_id, amount)
        new_progress = player.obsession.get_progress_percentage()
        
        # 获取条件描述
        condition_desc = ""
        for condition in player.obsession.conditions:
            if condition.condition_type == condition_type and condition.target_id == target_id:
                condition_desc = condition.description
                break
        
        results.append(f"[执念] {player.obsession.name} - {condition_desc} 进度 +{amount}")
        
        # 触发UI提示（如果当前在地图视图或叙事视图）
        print(f"[DEBUG] 尝试触发执念UI通知: {player.obsession.name}, 进度 {old_progress:.0f}% -> {new_progress:.0f}%")
        ObsessionEffectExecutor._trigger_map_notification(player, old_progress, new_progress)
        
        # 检查是否完成
        if player.obsession.check_all_conditions():
            player.obsession.is_completed = True
            results.append(f"[执念] ✨ 执念「{player.obsession.name}」已完成！")
            results.append(f"[执念] {player.obsession.completion_text}")
            
            # 应用奖励
            reward_results = ObsessionEffectExecutor._apply_obsession_rewards(player)
            results.extend(reward_results)
        
        return results
    
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
            print(f"[DEBUG] 获取窗口: {window is not None}")
            if window and hasattr(window, 'current_view'):
                current_view = window.current_view
                print(f"[DEBUG] 当前视图类型: {type(current_view).__name__}")
                # 检查当前视图是否是 MapView 或其子类，或者是 NarrativeSceneView
                if hasattr(current_view, 'show_obsession_progress_change'):
                    print(f"[DEBUG] 直接调用视图的 show_obsession_progress_change")
                    is_completed = player.obsession.check_all_conditions()
                    current_view.show_obsession_progress_change(
                        old_progress, 
                        new_progress, 
                        player.obsession.name,
                        is_completed
                    )
                elif hasattr(current_view, 'map_view') and hasattr(current_view.map_view, 'show_obsession_progress_change'):
                    # 处理 MapSceneView 包装的情况
                    print(f"[DEBUG] 调用 MapSceneView.map_view 的 show_obsession_progress_change")
                    is_completed = player.obsession.check_all_conditions()
                    current_view.map_view.show_obsession_progress_change(
                        old_progress, 
                        new_progress, 
                        player.obsession.name,
                        is_completed
                    )
                elif hasattr(current_view, 'narrative_renderer') and hasattr(current_view.narrative_renderer, 'update_obsession_progress_change'):
                    # 处理 NarrativeSceneView 的情况
                    print(f"[DEBUG] 调用 NarrativeSceneView.narrative_renderer 的 update_obsession_progress_change")
                    is_completed = player.obsession.check_all_conditions()
                    current_view.narrative_renderer.update_obsession_progress_change(
                        old_progress, 
                        new_progress, 
                        player.obsession.name,
                        is_completed
                    )
                else:
                    print(f"[DEBUG] 警告：当前视图没有发现执念通知方法")
            else:
                print(f"[DEBUG] 警告：无法获取窗口或当前视图")
        except Exception as e:
            print(f"[执念效果] 触发UI通知失败: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def _check_obsession_completion(player: Entity) -> List[str]:
        """
        检查执念是否完成
        
        Args:
            player: 玩家实体
            
        Returns:
            效果描述列表
        """
        results = []
        
        if not player.obsession:
            return results
        
        if player.obsession.is_completed:
            results.append(f"[执念] 执念「{player.obsession.name}」已完成")
        else:
            progress = player.obsession.get_progress_percentage()
            results.append(f"[执念] 执念「{player.obsession.name}」进度: {progress:.0f}%")
        
        return results
    
    @staticmethod
    def _apply_obsession_rewards(player: Entity) -> List[str]:
        """
        应用执念完成奖励
        
        Args:
            player: 玩家实体
            
        Returns:
            效果描述列表
        """
        results = []
        
        if not player.obsession or not player.obsession.rewards:
            return results
        
        for reward in player.obsession.rewards:
            reward_type = reward.reward_type
            value = reward.value
            description = reward.description
            
            if reward_type == "stat_bonus":
                # 应用属性加成
                if isinstance(value, dict):
                    for stat_name, bonus in value.items():
                        if hasattr(player.stats, stat_name):
                            setattr(player.stats, stat_name, getattr(player.stats, stat_name) + bonus)
                            results.append(f"[执念奖励] {stat_name} +{bonus}")
            
            elif reward_type == "special_card":
                # 获得特殊卡牌
                results.append(f"[执念奖励] 获得特殊卡牌: {value}")
                # TODO: 实际添加卡牌到牌库
            
            elif reward_type == "title":
                # 获得称号
                results.append(f"[执念奖励] 获得称号: {value}")
            
            else:
                results.append(f"[执念奖励] {description}")
        
        return results


# 便捷函数
def execute_obsession_effects(effects: List[Dict[str, Any]], player: Entity, battle_log=None) -> List[str]:
    """
    执行执念相关效果列表
    
    Args:
        effects: 效果列表
        player: 玩家实体
        battle_log: 战斗日志（可选）
        
    Returns:
        效果描述列表
    """
    executor = ObsessionEffectExecutor()
    all_results = []
    
    for effect in effects:
        if effect.get("type", "").startswith("obsession") or effect.get("type") in [
            "update_obsession_progress",
            "check_obsession_completion"
        ]:
            results = executor.execute_effect(effect, player, battle_log)
            all_results.extend(results)
    
    return all_results

"""
卡牌效果执行器模块
将卡牌效果与具体游戏系统（BattleSystem、TileMap 等）解耦
所有卡牌效果通过此执行器统一处理，支持多场景复用
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from config import CardTag, BuffType, TargetType
from game_context import GameContext, SceneType


@dataclass
class EffectResult:
    """效果执行结果"""
    success: bool = True
    message: str = ""
    log_level: int = 0  # 0=重要，1=普通，2=详细
    color_key: str = "normal"  # critical_success, success, failure, etc.


class EffectExecutor:
    """
    卡牌效果执行器
    将卡牌效果与具体游戏系统解耦，支持多场景复用
    """
    
    def __init__(self, context: GameContext):
        """
        初始化效果执行器
        
        Args:
            context: 游戏上下文对象
        """
        self.context = context
    
    def execute(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """
        执行单个效果
        
        Args:
            effect: 效果字典（来自卡牌的 effects 列表）
            source: 效果来源（通常是 Entity）
            targets: 目标列表
        
        Returns:
            效果执行结果列表
        """
        effect_type = effect.get("type", "")
        
        # 根据效果类型分发到不同的处理器
        handler = self._get_handler(effect_type)
        if handler:
            return handler(effect, source, targets)
        else:
            return [EffectResult(
                success=False,
                message=f"未知效果类型：{effect_type}",
                log_level=1,
                color_key="failure"
            )]
    
    def _get_handler(self, effect_type: str) -> Optional[Callable]:
        """获取效果处理器"""
        handlers = {
            "emy_dmg": self._handle_enemy_damage,
            "self_heal": self._handle_self_heal,
            "self_block": self._handle_self_block,
            "emy_debuff": self._handle_enemy_debuff,
            "self_buff": self._handle_self_buff,
            "self_resource": self._handle_self_resource,
            "ally_heal": self._handle_ally_heal,
            "aoe_damage": self._handle_aoe_damage,
            "movement": self._handle_movement,
        }
        return handlers.get(effect_type)
    
    def _roll_dice(self, dice_expr: str) -> int:
        """掷骰子"""
        if not dice_expr:
            return 0
        
        try:
            from dice_system import roll_dice_sum
            parts = dice_expr.lower().split('d')
            if len(parts) == 2:
                num_dice = int(parts[0])
                sides = int(parts[1])
                return roll_dice_sum(num_dice, sides)
            return 0
        except (ValueError, IndexError, ImportError):
            return 0
    
    def _get_stat_bonus(self, source: Any, stat_ratios: Dict[str, float]) -> int:
        """计算属性加值"""
        if not stat_ratios or not hasattr(source, 'stats'):
            return 0
        
        total_bonus = 0
        stats = source.stats
        
        if "str" in stat_ratios:
            total_bonus += int(stats.get_modifier('strength') * stat_ratios["str"])
        if "dex" in stat_ratios:
            total_bonus += int(stats.get_modifier('dexterity') * stat_ratios["dex"])
        if "int" in stat_ratios:
            total_bonus += int(stats.get_modifier('intelligence') * stat_ratios["int"])
        if "cha" in stat_ratios:
            total_bonus += int(stats.get_modifier('charisma') * stat_ratios["cha"])
        
        return total_bonus
    
    def _handle_enemy_damage(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """处理敌方伤害效果"""
        results = []
        dice_expr = effect.get("dice", "")
        
        if not dice_expr:
            return results
        
        base_damage = self._roll_dice(dice_expr)
        
        # 应用属性加值
        stat_ratios = effect.get("stat_ratios", {})
        stat_bonus = self._get_stat_bonus(source, stat_ratios)
        total_damage = base_damage + stat_bonus
        
        # 对每个目标造成伤害
        for target in targets:
            if hasattr(target, 'take_damage'):
                target.take_damage(total_damage, source=source, battle_log=self.context.battle_log)
                results.append(EffectResult(
                    success=True,
                    message=f"{source.name}对{target.name}造成{total_damage}点伤害",
                    log_level=0,
                    color_key="success"
                ))
        
        return results
    
    def _handle_self_heal(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """处理自我治疗效果"""
        results = []
        
        # 获取治疗量（骰子或固定值）
        dice_expr = effect.get("dice", "")
        if dice_expr:
            amount = self._roll_dice(dice_expr)
        else:
            amount_value = effect.get("amount", 0)
            if isinstance(amount_value, str):
                amount = self._roll_dice(amount_value)
            else:
                amount = amount_value
        
        # 应用属性加值
        stat_ratios = effect.get("stat_ratios", {})
        stat_bonus = self._get_stat_bonus(source, stat_ratios)
        total_heal = amount + stat_bonus
        
        if hasattr(source, 'heal'):
            source.heal(total_heal, battle_log=self.context.battle_log)
            results.append(EffectResult(
                success=True,
                message=f"{source.name}恢复了{total_heal}点生命值",
                log_level=0,
                color_key="success"
            ))
        
        return results
    
    def _handle_self_block(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """处理自我格挡效果"""
        results = []
        
        # 获取格挡值（骰子或固定值）
        dice_expr = effect.get("dice", "")
        if dice_expr:
            block_amount = self._roll_dice(dice_expr)
        else:
            amount_value = effect.get("amount", 0)
            if isinstance(amount_value, str):
                block_amount = self._roll_dice(amount_value)
            else:
                block_amount = amount_value
        
        # 应用属性加值
        stat_ratios = effect.get("stat_ratios", {})
        stat_bonus = self._get_stat_bonus(source, stat_ratios)
        total_block = block_amount + stat_bonus
        
        if hasattr(source, 'add_block'):
            source.add_block(total_block)
            results.append(EffectResult(
                success=True,
                message=f"{source.name}获得了{total_block}点格挡",
                log_level=0,
                color_key="success"
            ))
        
        return results
    
    def _handle_enemy_debuff(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """处理敌方 Debuff 效果"""
        results = []
        
        buff_type_str = effect.get("buff_type", "")
        stacks = effect.get("stacks", 1)
        duration = effect.get("duration", -1)
        
        # 查找对应的 BuffType
        buff_type = None
        for bt in BuffType:
            if bt.value == buff_type_str:
                buff_type = bt
                break
        
        if not buff_type:
            return results
        
        from models import Buff
        
        for target in targets:
            if hasattr(target, 'apply_buff'):
                buff = Buff(buff_type=buff_type, stacks=stacks, duration=duration)
                target.apply_buff(buff)
                results.append(EffectResult(
                    success=True,
                    message=f"{source.name}对{target.name}施加了{stacks}层{buff_type.name}",
                    log_level=0,
                    color_key="failure"
                ))
        
        return results
    
    def _handle_self_buff(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """处理自我 Buff 效果"""
        results = []
        
        buff_type_str = effect.get("buff_type", "")
        stacks = effect.get("stacks", 1)
        duration = effect.get("duration", -1)
        
        # 查找对应的 BuffType
        buff_type = None
        for bt in BuffType:
            if bt.value == buff_type_str:
                buff_type = bt
                break
        
        if not buff_type:
            return results
        
        from models import Buff
        
        if hasattr(source, 'apply_buff'):
            buff = Buff(buff_type=buff_type, stacks=stacks, duration=duration)
            source.apply_buff(buff)
            results.append(EffectResult(
                success=True,
                message=f"{source.name}获得了{stacks}层{buff_type.name}",
                log_level=0,
                color_key="success"
            ))
        
        return results
    
    def _handle_self_resource(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """处理自我资源效果（抽牌、恢复 MP 等）"""
        results = []
        
        # 处理抽牌效果
        draw_count = effect.get("draw", 0)
        if draw_count > 0 and hasattr(source, 'deck') and hasattr(source, 'hand'):
            import random
            
            available_cards = [c for c in source.deck if not hasattr(c, 'permanent') or not c.permanent]
            
            # 如果卡组不足，先从弃牌堆洗牌
            if len(available_cards) < draw_count and hasattr(source, 'discard_pile') and len(source.discard_pile) > 0:
                source.deck.extend(source.discard_pile)
                random.shuffle(source.deck)
                source.discard_pile.clear()
                available_cards = [c for c in source.deck if not hasattr(c, 'permanent') or not c.permanent]
            
            actual_draw = min(draw_count, len(available_cards))
            
            if actual_draw > 0:
                drawn_cards = random.sample(available_cards, actual_draw)
                for card in drawn_cards:
                    if card in source.deck:
                        source.deck.remove(card)
                        source.hand.append(card)
                
                results.append(EffectResult(
                    success=True,
                    message=f"{source.name}抽取了{actual_draw}张卡牌",
                    log_level=0,
                    color_key="success"
                ))
        
        # 处理 MP 恢复效果
        restore_mp = effect.get("restore_mp", 0)
        if restore_mp > 0 and hasattr(source, 'mp'):
            old_mp = source.mp
            source.mp = min(source.mp + restore_mp, source.max_mp)
            actual_restore = source.mp - old_mp
            results.append(EffectResult(
                success=True,
                message=f"{source.name}恢复了{actual_restore}点 MP",
                log_level=0,
                color_key="success"
            ))
        
        return results
    
    def _handle_ally_heal(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """处理友军治疗效果"""
        results = []
        
        dice_expr = effect.get("dice", "")
        if dice_expr:
            amount = self._roll_dice(dice_expr)
        else:
            amount_value = effect.get("amount", 0)
            if isinstance(amount_value, str):
                amount = self._roll_dice(amount_value)
            else:
                amount = amount_value
        
        stat_ratios = effect.get("stat_ratios", {})
        stat_bonus = self._get_stat_bonus(source, stat_ratios)
        total_heal = amount + stat_bonus
        
        for target in targets:
            if hasattr(target, 'heal') and target != source:
                target.heal(total_heal, battle_log=self.context.battle_log)
                results.append(EffectResult(
                    success=True,
                    message=f"{source.name}为{target.name}恢复了{total_heal}点生命值",
                    log_level=0,
                    color_key="success"
                ))
        
        return results
    
    def _handle_aoe_damage(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """处理 AOE 伤害效果"""
        results = []
        
        dice_expr = effect.get("dice", "")
        if not dice_expr:
            return results
        
        base_damage = self._roll_dice(dice_expr)
        stat_ratios = effect.get("stat_ratios", {})
        stat_bonus = self._get_stat_bonus(source, stat_ratios)
        total_damage = base_damage + stat_bonus
        
        for target in targets:
            if hasattr(target, 'take_damage'):
                target.take_damage(total_damage, source=source, battle_log=self.context.battle_log)
                results.append(EffectResult(
                    success=True,
                    message=f"{source.name}对{target.name}造成{total_damage}点 AOE 伤害",
                    log_level=0,
                    color_key="success"
                ))
        
        return results
    
    def _handle_movement(self, effect: Dict[str, Any], source: Any, targets: List[Any]) -> List[EffectResult]:
        """处理移动效果"""
        results = []
        
        if not self.context.is_combat:
            # 非战斗场景的移动处理可以不同
            return results
        
        distance = effect.get("distance", 0)
        direction = effect.get("direction", "forward")
        
        # 移动逻辑需要访问 tile_map 和实体位置
        if self.context.tile_map and hasattr(source, 'position'):
            old_pos = source.position
            # 这里可以调用 tile_map 的移动验证方法
            # 简化处理：直接更新位置（实际应该验证）
            new_x, new_y = old_pos
            if direction == "forward":
                new_x += distance
            elif direction == "backward":
                new_x -= distance
            
            # 验证新位置是否有效
            if self.context.tile_map.is_valid_position(new_x, new_y):
                source.position = (new_x, new_y)
                results.append(EffectResult(
                    success=True,
                    message=f"{source.name}移动到了({new_x}, {new_y})",
                    log_level=0,
                    color_key="success"
                ))
            else:
                results.append(EffectResult(
                    success=False,
                    message=f"{source.name}无法移动到无效位置",
                    log_level=1,
                    color_key="failure"
                ))
        
        return results


class CardEffectExecutor:
    """
    卡牌效果总执行器
    协调多个 EffectExecutor，处理完整的卡牌效果列表
    """
    
    def __init__(self, context: GameContext):
        """
        初始化卡牌效果执行器
        
        Args:
            context: 游戏上下文对象
        """
        self.context = context
        self.effect_executor = EffectExecutor(context)
    
    def execute_card_effects(self, card: Any, source: Any, selected_targets: List[Any]) -> List[EffectResult]:
        """
        执行卡牌的所有效果
        
        Args:
            card: 卡牌对象
            source: 卡牌使用者
            selected_targets: 选定的目标列表
        
        Returns:
            所有效果的执行结果列表
        """
        all_results = []
        
        effects = getattr(card, 'effects', [])
        
        # 处理结构化效果列表
        if isinstance(effects, list):
            for effect in effects:
                results = self.effect_executor.execute(effect, source, selected_targets)
                all_results.extend(results)
        
        return all_results
    
    def can_play_card(self, card: Any, source: Any, targets: List[Any]) -> tuple:
        """
        检查卡牌是否可以打出
        
        Args:
            card: 卡牌对象
            source: 卡牌使用者
            targets: 目标列表
        
        Returns:
            (can_play: bool, reason: str)
        """
        # 检查 AP 是否足够
        ap_cost = getattr(card, 'ap_cost', 0)
        if hasattr(source, 'ap') and source.ap < ap_cost:
            return False, f"AP 不足（需要{ap_cost}，当前{source.ap}）"
        
        # 检查 MP 是否足够（法术卡牌）
        mp_cost = getattr(card, 'mp_cost', 0)
        if mp_cost > 0 and hasattr(source, 'mp') and source.mp < mp_cost:
            return False, f"MP 不足（需要{mp_cost}，当前{source.mp}）"
        
        # 检查目标有效性（仅在战斗场景且目标类型为敌人时严格检查）
        if self.context.is_combat:
            target_type = getattr(card, 'target_type', TargetType.ENEMY)
            
            if target_type == TargetType.ENEMY:
                if not any(t in self.context.enemies for t in targets):
                    # 如果不是严格敌人检查，至少要有目标
                    if len(targets) == 0:
                        return False, "必须选择目标"
            elif target_type == TargetType.ALLY:
                if not any(t in self.context.allies for t in targets):
                    return False, "必须选择友军作为目标"
            elif target_type == TargetType.SELF:
                if source not in targets:
                    return False, "必须以自己为目标"
        
        return True, ""

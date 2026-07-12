"""
叙事节点系统模块
提供检定叙事框架，包括节点、动作标签、结果引擎等
"""
import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class DifficultyLevel(Enum):
    """难度等级枚举"""
    EASY = "简单"          # DN 10
    MEDIUM = "中等"        # DN 12
    HARD = "困难"          # DN 16
    VERY_HARD = "极难"     # DN 20
    IMPOSSIBLE = "不可能"  # DN 25


# 难度等级对应的DN值
DIFFICULTY_DN_MAP = {
    DifficultyLevel.EASY: 10,
    DifficultyLevel.MEDIUM: 12,
    DifficultyLevel.HARD: 16,
    DifficultyLevel.VERY_HARD: 20,
    DifficultyLevel.IMPOSSIBLE: 25,
}


class CheckType(Enum):
    """检定类型枚举"""
    STRENGTH = "力量"       # 力量检定
    DEXTERITY = "敏捷"      # 敏捷检定
    INTELLIGENCE = "心智"   # 心智检定
    CHARISMA = "魅力"       # 魅力检定
    LUCK = "幸运"           # 幸运检定
    COMPOSITE = "复合"      # 复合检定（多个属性组合）


@dataclass
class NarrativeAction:
    """叙事动作定义"""
    name: str                           # 动作名称，如 "贿赂", "威胁", "火焰箭"
    description: str                    # 动作描述
    tags: List[str] = field(default_factory=list)  # 动作标签列表
    check_type: Optional[CheckType] = None  # 检定类型（None表示无需检定）
    difficulty: Optional[DifficultyLevel] = None  # 难度等级
    stat_ratios: Dict[str, float] = field(default_factory=dict)  # 属性比例 {"str": 1.0, "dex": 0.5}
    is_hidden: bool = False             # 是否为隐藏选项（需要特定条件才显示）
    hidden_condition: Optional[str] = None  # 隐藏条件的描述
    required_tags: List[str] = field(default_factory=list)  # 揭示此隐藏动作所需的卡牌标签
    
    def get_dn(self) -> int:
        """获取难度值"""
        if self.difficulty:
            return DIFFICULTY_DN_MAP.get(self.difficulty, 12)
        return 12  # 默认中等难度


@dataclass
class NarrativeResult:
    """叙事结果定义
    
    effects 字段命名规范（Effects Field Schema）：
    每个 effect 都是一个字典，必须含 "type" 键，其余字段依 type 而定：
    
    通用规则：
      - 主要数值用 "value"（int/float/bool）
      - 持续回合数用 "duration"（int）
      - 敌人/物品/位置/buff/debuff 等语义对象 ID 用对应语义字段名（如下）
    
    常用 effect 类型及字段：
      gain_reputation       / value: int          — 获得声誉
      gain_fear_reputation  / value: int          — 获得威慑声誉
      gain_infamy           / value: int          — 获得恶名
      gain_knowledge        / value: int          — 获得知识点
      gain_experience       / value: int          — 获得经验
      gain_item             / item: str           — 获得物品（物品ID）
      lose_item             / item: str           — 失去物品（物品ID）
      gain_blessing         / blessing: str       — 获得祝福（祝福ID）
      gain_revelation       / revelation: str     — 获得启示（启示ID）
      gain_buff             / buff: str, duration: int  — 获得增益状态
      apply_debuff          / debuff: str, duration: int — 施加减益状态
      take_damage           / value: int          — 受到伤害
      heal                  / value: int          — 恢复生命
      mental_damage         / value: int          — 精神伤害
      stat_bonus_temp       / stat: str, value: int, duration: int — 临时属性加成
      trigger_combat        / enemy: str          — 触发战斗（敌人ID）
      stealth_entry         / value: true         — 隐秘进入
      suspicion_raised      / value: int          — 引发怀疑
      delay_entry           / value: true         — 延迟进入
      lose_time             / value: int          — 消耗时间
      morale_decrease       / value: int          — 士气下降
      location_locked       / location: str       — 封锁地点
      confusion             / duration: int       — 困惑状态
      village_loss_increase / value: int          — 村庄损失增加
      temple_damage         / value: int          — 圣地受损
      friendly_fire         / value: int          — 误伤
      defender_retreat      / value: int          — 守卫撤退
      update_obsession_progress / condition_type: str, target_id: str, amount: int
                            — 更新执念进度（当前API；未来将迁移至涌现式执念系统的 accumulate_signal 接口）
    
    TODO: 当"涌现式执念系统"（ObsessionTendency/EmergentObsessionState）合并后，
    需将 update_obsession_progress 迁移为对应的 signal_type/amount 接口。
    """
    outcome_level: str                  # 结果等级："大成功", "成功", "半成功", "失败", "大失败"
    text: str                           # 结果文本描述
    effects: List[Dict[str, Any]] = field(default_factory=list)  # 效果列表（如状态变化、物品获得等）
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "outcome_level": self.outcome_level,
            "text": self.text,
            "effects": self.effects
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'NarrativeResult':
        """从字典反序列化"""
        return NarrativeResult(
            outcome_level=data["outcome_level"],
            text=data["text"],
            effects=data.get("effects", [])
        )


@dataclass
class NarrativeNode:
    """叙事节点定义"""
    node_id: str                        # 节点唯一ID
    title: str                          # 节点标题
    description: str                    # 节点描述
    scene_image: Optional[str] = None   # 场景图片路径（可选）
    tags: List[str] = field(default_factory=list)  # 节点标签列表
    map_node_id: Optional[str] = None   # 对应的地图节点ID（可选）
    actions: List[NarrativeAction] = field(default_factory=list)  # 可用动作列表
    results_pool: Dict[str, List[NarrativeResult]] = field(default_factory=dict)  # 结果池：动作标签 -> 结果列表
    next_nodes: Dict[str, str] = field(default_factory=dict)  # 下一节点映射：结果等级 -> 节点ID（"__end__"表示内联结束）
    is_end_node: bool = False           # 是否为结束节点
    end_summary: Optional[str] = None  # 内联结束时的收尾文案（新格式）
    
    def get_action_by_name(self, name: str) -> Optional[NarrativeAction]:
        """根据名称获取动作"""
        for action in self.actions:
            if action.name == name:
                return action
        return None
    
    def get_results_for_action(self, action: NarrativeAction) -> List[NarrativeResult]:
        """
        根据动作获取对应的结果池
        
        优先级：
        1. 硬编码的动作名称（如"火焰箭"）
        2. 动作的特定标签（如"火球术"、"点火"）
        3. 通用的"火焰"标签（fallback）
        """
        # 优先级1: 首先尝试通过动作名称查找（硬编码的特定结果）
        if action.name in self.results_pool:
            return self.results_pool[action.name]
        
        # 优先级2: 然后通过动作的非通用标签查找（排除"火焰"这个通用标签）
        for tag in action.tags:
            # 跳过通用标签，优先使用特定标签
            if tag != "火焰" and tag in self.results_pool:
                return self.results_pool[tag]
        
        # 优先级3: 最后尝试使用"火焰"通用标签（fallback机制）
        if "火焰" in self.results_pool:
            return self.results_pool["火焰"]
        
        # 如果都没有，返回空列表
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "node_id": self.node_id,
            "title": self.title,
            "description": self.description,
            "scene_image": self.scene_image,
            "tags": self.tags,
            "map_node_id": self.map_node_id,
            "actions": [
                {
                    "name": a.name,
                    "description": a.description,
                    "tags": a.tags,
                    "check_type": a.check_type.value if a.check_type else None,
                    "difficulty": a.difficulty.value if a.difficulty else None,
                    "stat_ratios": a.stat_ratios,
                    "is_hidden": a.is_hidden,
                    "hidden_condition": a.hidden_condition,
                    "required_tags": a.required_tags
                }
                for a in self.actions
            ],
            "results_pool": {
                key: [r.to_dict() for r in results]
                for key, results in self.results_pool.items()
            },
            "next_nodes": self.next_nodes,
            "is_end_node": self.is_end_node
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any], templates: Optional[Dict[str, Any]] = None) -> 'NarrativeNode':
        """从字典反序列化
        
        Args:
            data: 节点数据字典
            templates: 可选的 outcome_templates 字典，用于解析模板引用。
                       默认为 None；Python 最佳实践是用 None 而非 {} 作为可变类型默认值，
                       以防止多次调用之间意外共享同一个字典对象。
        """
        if templates is None:
            templates = {}  # 在函数内部初始化，确保每次调用都是独立的新字典

        actions = []
        for action_data in data.get("actions", []):
            check_type = None
            if action_data.get("check_type"):
                try:
                    check_type = CheckType(action_data["check_type"])
                except ValueError:
                    pass
            
            difficulty = None
            if action_data.get("difficulty"):
                try:
                    difficulty = DifficultyLevel(action_data["difficulty"])
                except ValueError:
                    pass
            
            actions.append(NarrativeAction(
                name=action_data["name"],
                description=action_data["description"],
                tags=action_data.get("tags", []),
                check_type=check_type,
                difficulty=difficulty,
                stat_ratios=action_data.get("stat_ratios", {}),
                is_hidden=action_data.get("is_hidden", False),
                hidden_condition=action_data.get("hidden_condition"),
                required_tags=action_data.get("required_tags", [])
            ))
        
        results_pool = {}
        for key, results_data in data.get("results_pool", {}).items():
            if isinstance(results_data, list):
                # 旧格式：[{"outcome_level": ..., "text": ..., "effects": ...}, ...]
                results_pool[key] = [NarrativeResult.from_dict(r) for r in results_data]
            elif isinstance(results_data, dict) and "$template" in results_data:
                # 模板引用格式：{"$template": "template_id", "params": {...}}
                template_id = results_data["$template"]
                params = results_data.get("params", {})
                if template_id in templates:
                    results_pool[key] = NarrativeNode._resolve_template(templates[template_id], params)
                else:
                    results_pool[key] = []
            elif isinstance(results_data, dict):
                # 新格式：{"大成功": {"text": ..., "effects": [...]}, ...}
                results_pool[key] = [
                    NarrativeResult(
                        outcome_level=level,
                        text=level_data["text"],
                        effects=level_data.get("effects", [])
                    )
                    for level, level_data in results_data.items()
                ]
        
        return NarrativeNode(
            node_id=data["node_id"],
            title=data["title"],
            description=data["description"],
            scene_image=data.get("scene_image"),
            tags=data.get("tags", []),
            map_node_id=data.get("map_node_id"),
            actions=actions,
            results_pool=results_pool,
            next_nodes=data.get("next_nodes", {}),
            is_end_node=data.get("is_end_node", False),
            end_summary=data.get("end_summary")
        )

    @staticmethod
    def _resolve_template(template: Dict[str, Any], params: Dict[str, Any]) -> List[NarrativeResult]:
        """将 outcome_template 解析为 NarrativeResult 列表，支持参数替换。
        
        Args:
            template: 模板字典，键为结果等级，值为 {"text": ..., "effects": [...]}
            params: 替换参数字典，如 {"action_name": "火焰箭"}。
                    模板文本中使用 {param_key} 占位符；params 为空时直接使用原文本。
                    例：模板文本 "{action_name}点燃了草丛" + params {"action_name": "火球术"}
                        → "火球术点燃了草丛"
        """
        results = []
        for level, result_data in template.items():
            text = result_data["text"]
            for param_key, param_val in params.items():
                text = text.replace(f"{{{param_key}}}", str(param_val))
            results.append(NarrativeResult(
                outcome_level=level,
                text=text,
                effects=result_data.get("effects", [])
            ))
        return results


class NarrativeResultEngine:
    """五级结果引擎 - 根据动作和检定结果生成叙事输出"""
    
    # 开发者作弊模式：开启后所有检定都为大成功
    _debug_god_mode: bool = False
    
    @staticmethod
    def enable_debug_god_mode():
        """开启开发者作弊模式（所有检定大成功）"""
        NarrativeResultEngine._debug_god_mode = True
        print("\n[开发者] ⚡ 作弊模式已开启！所有检定将自动大成功！")
    
    @staticmethod
    def disable_debug_god_mode():
        """关闭开发者作弊模式"""
        NarrativeResultEngine._debug_god_mode = False
        print("\n[开发者] 作弊模式已关闭")
    
    @staticmethod
    def is_debug_god_mode_enabled() -> bool:
        """检查作弊模式是否开启"""
        return NarrativeResultEngine._debug_god_mode
    
    @staticmethod
    def check_hand_for_tags(hand, required_tags: List[str]) -> bool:
        """
        检查手牌中是否包含所需的标签
        
        Args:
            hand: 手牌列表（Card对象）
            required_tags: 需要的标签列表
            
        Returns:
            如果手牌中有任何一张卡牌包含所需标签则返回True
        """
        if not required_tags:
            return True
        
        # print(f"    [DEBUG] check_hand_for_tags: 需要标签 {required_tags}")
        
        for card in hand:
            # 检查卡牌是否有tags属性
            if hasattr(card, 'tags') and card.tags:
                # print(f"    [DEBUG]   检查卡牌 '{card.name}' 的标签: {card.tags}")
                for tag in card.tags:
                    # 检查标签是否匹配（支持CardTag枚举和字符串）
                    tag_str = tag.value if hasattr(tag, 'value') else str(tag)
                    # print(f"    [DEBUG]     标签: '{tag_str}'")
                    if tag_str in required_tags:
                        # print(f"    [DEBUG]     ✓ 找到匹配标签!")
                        return True
            # else:
                # print(f"    [DEBUG]   卡牌 '{card.name}' 没有tags属性或为空")
        
        # print(f"    [DEBUG]   ✗ 未找到所需标签")
        return False
    
    @staticmethod
    def get_outcome_level(final_result: int, dn: int) -> str:
        """
        根据最终结果和难度值确定结果等级
        
        Args:
            final_result: 最终结果（骰子+加值）
            dn: 难度值
            
        Returns:
            结果等级字符串
        """
        if final_result >= dn + 8:
            return "大成功"
        elif final_result >= dn:
            return "成功"
        elif final_result >= dn - 4:
            return "半成功"
        elif final_result > dn - 9:
            return "失败"
        else:  # final_result <= dn - 9
            return "大失败"
    
    @staticmethod
    def calculate_stat_bonus(stats: Any, stat_ratios: Dict[str, float]) -> int:
        """
        计算属性加值
        
        Args:
            stats: 角色属性对象
            stat_ratios: 属性比例字典
            
        Returns:
            属性加值总和
        """
        if not stat_ratios:
            return 0
        
        total_bonus = 0
        
        # 力量加值
        if "str" in stat_ratios:
            str_mod = (stats.strength - 10) // 2
            total_bonus += int(str_mod * stat_ratios["str"])
        
        # 敏捷加值
        if "dex" in stat_ratios:
            dex_mod = (stats.dexterity - 10) // 2
            total_bonus += int(dex_mod * stat_ratios["dex"])
        
        # 心智加值
        if "int" in stat_ratios:
            int_mod = (stats.intelligence - 10) // 2
            total_bonus += int(int_mod * stat_ratios["int"])
        
        # 魅力加值
        if "cha" in stat_ratios:
            cha_mod = (stats.charisma - 10) // 2
            total_bonus += int(cha_mod * stat_ratios["cha"])
        
        # 幸运加值
        if "luck" in stat_ratios:
            luck_mod = (stats.luck - 10) // 2
            total_bonus += int(luck_mod * stat_ratios["luck"])
        
        return total_bonus
    
    @staticmethod
    def perform_check(action: NarrativeAction, stats: Any) -> Tuple[int, int, int, str]:
        """
        执行检定
        
        Args:
            action: 叙事动作
            stats: 角色属性对象
            
        Returns:
            (dice_total, stat_bonus, final_result, outcome_level)
        """
        from dice_system import roll_dice_sum
        
        # 检查是否开启作弊模式
        if NarrativeResultEngine._debug_god_mode:
            # 作弊模式：直接返回大成功
            dn = action.get_dn()
            # 设置一个足够高的骰子值，确保必定大成功（dn + 8 以上）
            dice_total = dn + 10  # 保证超过大成功阈值
            stat_bonus = 0
            final_result = dice_total + stat_bonus
            outcome_level = "大成功"
            print(f"[开发者] ⚡ 作弊模式生效！强制大成功！")
            return dice_total, stat_bonus, final_result, outcome_level
        
        # 正常模式：掷2d10
        dice_total = roll_dice_sum(2, 10)
        
        # 计算属性加值
        stat_bonus = NarrativeResultEngine.calculate_stat_bonus(stats, action.stat_ratios)
        
        # 计算最终结果
        final_result = dice_total + stat_bonus
        
        # 获取难度值
        dn = action.get_dn()
        
        # 确定结果等级
        outcome_level = NarrativeResultEngine.get_outcome_level(final_result, dn)
        
        return dice_total, stat_bonus, final_result, outcome_level
    
    @staticmethod
    def generate_result(node: NarrativeNode, action: NarrativeAction, 
                       outcome_level: str, stats: Any = None) -> Optional[NarrativeResult]:
        """
        生成叙事结果
        
        Args:
            node: 叙事节点
            action: 叙事动作
            outcome_level: 结果等级
            stats: 角色属性（可选，用于日志）
            
        Returns:
            叙事结果对象，如果没有匹配的结果则返回None
        """
        # 获取该动作的结果池
        results = node.get_results_for_action(action)
        
        if not results:
            return None
        
        # 筛选出匹配结果等级的结果
        matching_results = [r for r in results if r.outcome_level == outcome_level]
        
        if not matching_results:
            # 如果没有精确匹配，尝试使用"通用"结果
            matching_results = [r for r in results if r.outcome_level == "通用"]
        
        if not matching_results:
            return None
        
        # 随机选择一个结果
        return random.choice(matching_results)


class NarrativeNodeManager:
    """叙事节点管理器 - 管理所有叙事节点的加载和查询"""
    
    def __init__(self):
        self.nodes: Dict[str, NarrativeNode] = {}
    
    def load_from_file(self, filepath: str):
        """从JSON文件加载叙事节点
        
        支持两种格式：
        1. 新格式（推荐）：{"outcome_templates": {...}, "nodes": [...]}
        2. 旧格式（兼容）：[{node}, ...] 或单个节点 {node}
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and "nodes" in data:
            # 新格式：包含 outcome_templates 和 nodes 的顶层对象
            templates = data.get("outcome_templates", {})
            nodes_list = data["nodes"]
            for node_data in nodes_list:
                node = NarrativeNode.from_dict(node_data, templates)
                self.nodes[node.node_id] = node
        elif isinstance(data, list):
            # 旧格式：节点列表
            for node_data in data:
                node = NarrativeNode.from_dict(node_data)
                self.nodes[node.node_id] = node
        else:
            # 旧格式：单个节点
            node = NarrativeNode.from_dict(data)
            self.nodes[node.node_id] = node
    
    def save_to_file(self, filepath: str):
        """保存所有节点到JSON文件"""
        data = [node.to_dict() for node in self.nodes.values()]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_node(self, node_id: str) -> Optional[NarrativeNode]:
        """根据ID获取节点"""
        return self.nodes.get(node_id)
    
    def add_node(self, node: NarrativeNode):
        """添加节点"""
        self.nodes[node.node_id] = node
    
    def remove_node(self, node_id: str):
        """移除节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
    
    def get_all_nodes(self) -> List[NarrativeNode]:
        """获取所有节点"""
        return list(self.nodes.values())
    
    def clear(self):
        """清空所有节点"""
        self.nodes.clear()


# ==================== 示例数据创建函数 ====================

def create_example_nodes() -> List[NarrativeNode]:
    """创建示例叙事节点"""
    nodes = []
    
    # 城门护卫节点
    gate_guard_node = NarrativeNode(
        node_id="gate_guard_001",
        title="城门护卫",
        description='你们终于抵达了城门。塔拉多城巍峨的城墙在地上投出阴影，走近城门，守卫顿了一下手中的戟，厉声道：“特拉多城无通行许可不可入内！”，你们面面相觑，该怎么办呢？',
        scene_image=None,
        tags=["城门", "守卫", "社交"],
        actions=[
            NarrativeAction(
                name="贿赂",
                description="这里是一点心意，还请您收下。",
                tags=["贿赂", "社交", "魅力"],
                check_type=CheckType.CHARISMA,
                difficulty=DifficultyLevel.MEDIUM,
                stat_ratios={"cha": 1.0}
            ),
            NarrativeAction(
                name="威胁",
                description="要不要尝尝我沙包大的拳头！",
                tags=["威胁", "战斗", "力量"],
                check_type=CheckType.STRENGTH,
                difficulty=DifficultyLevel.HARD,
                stat_ratios={"str": 1.0}
            ),
            NarrativeAction(
                name="火焰箭",
                description="将火焰箭射向旁边的草丛，并告诉护卫那里着火了，趁乱溜进去",
                tags=["火焰", "法术", "环境互动"],
                check_type=CheckType.COMPOSITE,
                difficulty=DifficultyLevel.MEDIUM,
                stat_ratios={"int": 0.5, "dex": 0.5},
                is_hidden=True,
                hidden_condition="仅当玩家将火焰箭拖入场景视图时显示"
            )
        ],
        results_pool={
            "贿赂": [
                NarrativeResult(
                    outcome_level="大成功",
                    text="守卫眼睛一亮，迅速收下金币，低声说：'快进去，别让人看见。'你顺利进入城内，还获得了守卫的好感。",
                    effects=[{"type": "gain_reputation", "value": 1}]
                ),
                NarrativeResult(
                    outcome_level="成功",
                    text="守卫掂量了一下金币的分量，点点头让开了道路。你顺利进入城内。",
                    effects=[]
                ),
                NarrativeResult(
                    outcome_level="半成功",
                    text="守卫收了钱，但还是要求检查你们的行李。经过一番盘查后，你们才得以进入。",
                    effects=[{"type": "lose_time", "value": 1}]
                ),
                NarrativeResult(
                    outcome_level="失败",
                    text="守卫冷笑一声：'就这点钱？想贿赂我？'他大声呼救，引来了更多守卫。",
                    effects=[{"type": "trigger_combat", "enemy": "city_guards"}]
                ),
                NarrativeResult(
                    outcome_level="大失败",
                    text="守卫大怒：'竟敢贿赂本官！'他立即下令逮捕你们，整个城门都被封锁了。",
                    effects=[{"type": "trigger_combat", "enemy": "city_guards_elite"}]
                )
            ],
            "威胁": [
                NarrativeResult(
                    outcome_level="大成功",
                    text="你展现出强大的气势，守卫吓得脸色苍白，连忙让开道路，甚至不敢直视你。",
                    effects=[{"type": "gain_fear_reputation", "value": 2}]
                ),
                NarrativeResult(
                    outcome_level="成功",
                    text="守卫犹豫了一下，最终还是选择明哲保身，让你们通过了。",
                    effects=[]
                ),
                NarrativeResult(
                    outcome_level="半成功",
                    text="守卫虽然害怕，但还是坚持原则，要求你们出示证件。僵持片刻后，一位军官过来解围。",
                    effects=[{"type": "delay_entry", "value": True}]
                ),
                NarrativeResult(
                    outcome_level="失败",
                    text="守卫被激怒了：'好大的胆子！'他吹响哨子，召集同伴准备战斗。",
                    effects=[{"type": "trigger_combat", "enemy": "city_guards"}]
                ),
                NarrativeResult(
                    outcome_level="大失败",
                    text="你刚要动手，就被守卫一脚踢中膝盖，摔倒在地。其他守卫蜂拥而上，将你们制服。",
                    effects=[{"type": "take_damage", "value": 5}, {"type": "trigger_combat", "enemy": "city_guards_elite"}]
                )
            ],
            "火焰箭": [
                NarrativeResult(
                    outcome_level="大成功",
                    text="火焰箭精准地射中草丛，火势迅速蔓延。守卫们惊慌失措地去救火，你们趁机溜进城门，无人察觉。",
                    effects=[{"type": "stealth_entry", "value": True}]
                ),
                NarrativeResult(
                    outcome_level="成功",
                    text="火焰箭点燃了草丛，守卫们的注意力被吸引过去。你们抓住机会快速通过城门。",
                    effects=[]
                ),
                NarrativeResult(
                    outcome_level="半成功",
                    text="火焰箭射中了目标，但火势不够大。一名守卫发现了异常，但在你们解释前，火堆吸引了其他人的注意。",
                    effects=[{"type": "suspicion_raised", "value": 1}]
                ),
                NarrativeResult(
                    outcome_level="失败",
                    text="火焰箭偏离了目标，落在守卫脚边。他立刻警觉起来，拔出武器质问你们。",
                    effects=[{"type": "trigger_combat", "enemy": "city_guards"}]
                ),
                NarrativeResult(
                    outcome_level="大失败",
                    text="火焰箭意外击中了城门的油桶，引发剧烈爆炸！你和守卫都被卷入火海。",
                    effects=[{"type": "take_damage", "value": 15}, {"type": "trigger_combat", "enemy": "city_guards_elite"}]
                )
            ]
        },
        next_nodes={
            "大成功": "city_interior_001",
            "成功": "city_interior_001",
            "半成功": "city_gate_delayed",
            "失败": "combat_city_guards",
            "大失败": "combat_city_guards_elite"
        },
        is_end_node=False
    )
    
    nodes.append(gate_guard_node)
    
    return nodes


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("叙事节点系统测试")
    print("=" * 60)
    
    # 创建示例节点
    nodes = create_example_nodes()
    
    # 创建节点管理器
    manager = NarrativeNodeManager()
    for node in nodes:
        manager.add_node(node)
    
    # 保存节点
    manager.save_to_file("narrative_nodes.json")
    print("\n✓ 已保存示例节点到 narrative_nodes.json")
    
    # 重新加载节点
    manager2 = NarrativeNodeManager()
    manager2.load_from_file("narrative_nodes.json")
    print("✓ 已从文件加载节点")
    
    # 获取节点
    node = manager2.get_node("gate_guard_001")
    if node:
        print(f"\n节点标题: {node.title}")
        print(f"节点描述: {node.description[:50]}...")
        print(f"可用动作数: {len(node.actions)}")
        
        for i, action in enumerate(node.actions, 1):
            print(f"\n动作{i}: {action.name}")
            print(f"  描述: {action.description}")
            print(f"  标签: {', '.join(action.tags)}")
            if action.check_type:
                print(f"  检定类型: {action.check_type.value}")
            if action.difficulty:
                print(f"  难度: {action.difficulty.value} (DN {action.get_dn()})")
            if action.is_hidden:
                print(f"  隐藏条件: {action.hidden_condition}")
    
    print("\n" + "=" * 60)

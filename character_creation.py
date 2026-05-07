"""
角色创建系统模块
包含职业选择、属性分配和初始装备选择界面
"""
import arcade
from typing import Dict, List, Optional, Tuple
from models import Entity, Stats, Equipment, Weapon, Armor, ControlType
from career_system import Career, CareerType, CareerFactory
from card_database import create_weapon_database, create_armor_database
from inventory import Inventory, InventoryItem, ItemType, ItemShape
from config import CONSTANTS, Rarity
from ui_scale import S, update_scale


class CharacterCreationView(arcade.View):
    """角色创建视图 - 全屏界面"""
    
    def __init__(self, on_character_created_callback):
        super().__init__()
        
        self.on_character_created = on_character_created_callback
        
        # 使用配置中自动检测的窗口尺寸
        self.window_width = CONSTANTS.WINDOW_WIDTH
        self.window_height = CONSTANTS.WINDOW_HEIGHT
        
        # 确保缩放单例与当前窗口同步
        update_scale(self.window_width, self.window_height)
        
        # 创建阶段: 0=职业选择, 1=属性分配, 2=装备选择
        self.creation_stage = 0
        
        # 角色数据
        self.selected_career: Optional[Career] = None
        self.character_name = "冒险者"
        self.stats = Stats(
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            luck=10
        )
        
        # 属性购买点数系统 (18点购买)
        self.available_points = 18
        self.base_stat = 10  # 基础属性值
        self.max_stat = 16   # 最大属性值
        
        # 选择的初始装备套装
        self.selected_equipment_set = 0  # 0=轻甲+刺剑, 1=中甲+匕首, 2=法袍
        
        # UI元素位置
        self._calculate_layout()
        
        # 悬停状态
        self.hovered_career_index = -1
        self.hovered_equipment_index = -1
    
    def _calculate_layout(self):
        """计算UI布局（所有绝对像素值通过 UIScale 换算，支持 4K/高 DPI）"""
        self.layout_center_x = self.window_width // 2
        self.layout_center_y = self.window_height // 2
        
        # 职业选择界面布局
        self.career_list_x = self.window_width * 0.25
        self.career_list_y_start = self.window_height * 0.7
        self.career_item_height = S.py(60)
        self.career_description_x = self.window_width * 0.55
        self.career_description_y = self.window_height * 0.5
        
        # 属性分配界面布局
        self.stat_row_height = S.py(80)
        self.stat_rows_start_y = self.window_height * 0.65
        
        # 装备选择界面布局
        self.equipment_option_height = S.py(150)
        self.equipment_options_start_y = self.window_height * 0.6
    
    def on_resize(self, width: int, height: int):
        """窗口尺寸变化时重新计算布局。"""
        self.window_width = width
        self.window_height = height
        self._calculate_layout()
    
    def on_draw(self):
        """绘制角色创建界面"""
        self.clear()
        
        # 绘制背景
        arcade.set_background_color(arcade.color.EERIE_BLACK)
        
        # 根据当前阶段绘制不同界面
        if self.creation_stage == 0:
            self._draw_career_selection()
        elif self.creation_stage == 1:
            self._draw_stat_allocation()
        elif self.creation_stage == 2:
            self._draw_equipment_selection()
    
    def _draw_career_selection(self):
        """绘制职业选择界面"""
        # 标题
        title_text = "选择你的职业"
        arcade.draw_text(
            title_text,
            self.layout_center_x,
            self.window_height * 0.9,
            arcade.color.GOLD,
            S.font(48),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # 获取所有职业
        careers = CareerFactory.get_all_careers()
        
        # 绘制职业列表（左侧）
        for i, career in enumerate(careers):
            y_pos = self.career_list_y_start - i * self.career_item_height
            
            # 检查是否悬停
            is_hovered = (i == self.hovered_career_index)
            
            # 绘制职业选项背景
            if is_hovered:
                arcade.draw_lrbt_rectangle_filled(
                    self.career_list_x - S.px(150),
                    self.career_list_x + S.px(150),
                    y_pos - S.py(25),
                    y_pos + S.py(25),
                    arcade.color.DARK_SLATE_GRAY
                )
            
            # 绘制职业名称
            color = arcade.color.LIGHT_BLUE if is_hovered else arcade.color.WHITE
            arcade.draw_text(
                career.name,
                self.career_list_x,
                y_pos,
                color,
                S.font(24),
                anchor_x="center",
                anchor_y="center",
                bold=is_hovered
            )
        
        # 绘制职业描述（右侧）
        if self.hovered_career_index >= 0 and self.hovered_career_index < len(careers):
            career = careers[self.hovered_career_index]
            
            # 职业名称
            arcade.draw_text(
                career.name,
                self.career_description_x,
                self.career_description_y + S.py(100),
                arcade.color.GOLD,
                S.font(36),
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
            
            # 职业描述
            desc_lines = self._wrap_text(career.description, 50)
            for i, line in enumerate(desc_lines):
                arcade.draw_text(
                    line,
                    self.career_description_x,
                    self.career_description_y + S.py(50) - i * S.py(30),
                    arcade.color.WHITE,
                    S.font(20),
                    anchor_x="center",
                    anchor_y="center"
                )
            
            # 被动技能
            if career.passives:
                passive_y = self.career_description_y - S.py(50)
                arcade.draw_text(
                    "被动技能:",
                    self.career_description_x,
                    passive_y,
                    arcade.color.LIGHT_GREEN,
                    S.font(24),
                    anchor_x="center",
                    anchor_y="center",
                    bold=True
                )
                
                for i, passive in enumerate(career.passives):
                    passive_y -= S.py(40)
                    arcade.draw_text(
                        f"• {passive.name}",
                        self.career_description_x,
                        passive_y,
                        arcade.color.YELLOW,
                        S.font(18),
                        anchor_x="center",
                        anchor_y="center",
                        bold=True
                    )
                    
                    # 被动描述
                    passive_desc_lines = self._wrap_text(passive.description, 45)
                    for j, line in enumerate(passive_desc_lines):
                        arcade.draw_text(
                            line,
                            self.career_description_x,
                            passive_y - S.py(25) - j * S.py(20),
                            arcade.color.LIGHT_GRAY,
                            S.font(16),
                            anchor_x="center",
                            anchor_y="center"
                        )
                    passive_y -= len(passive_desc_lines) * S.py(20)
        
        # 提示文字
        arcade.draw_text(
            "点击职业进行选择，然后点击右下角的'下一步'",
            self.layout_center_x,
            S.py(50),
            arcade.color.GRAY,
            S.font(16),
            anchor_x="center",
            anchor_y="center"
        )
        
        # 下一步按钮
        if self.selected_career:
            button_color = arcade.color.GREEN
            text_color = arcade.color.WHITE
        else:
            button_color = arcade.color.DARK_GRAY
            text_color = arcade.color.GRAY
        
        button_x = self.window_width * 0.85
        button_y = S.py(80)
        arcade.draw_lrbt_rectangle_filled(
            button_x - S.px(75), button_x + S.px(75),
            button_y - S.py(25), button_y + S.py(25),
            button_color
        )
        arcade.draw_text(
            "下一步",
            button_x,
            button_y,
            text_color,
            S.font(20),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
    
    def _draw_stat_allocation(self):
        """绘制属性分配界面"""
        # 标题
        arcade.draw_text(
            "分配属性点数",
            self.layout_center_x,
            self.window_height * 0.9,
            arcade.color.GOLD,
            S.font(48),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # 显示剩余点数
        points_text = f"剩余点数: {self.available_points}"
        color = arcade.color.GREEN if self.available_points > 0 else arcade.color.RED
        arcade.draw_text(
            points_text,
            self.layout_center_x,
            self.window_height * 0.82,
            color,
            S.font(32),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # 职业建议
        if self.selected_career:
            suggestion_text = f"{self.selected_career.name} 推荐属性:"
            arcade.draw_text(
                suggestion_text,
                self.layout_center_x,
                self.window_height * 0.76,
                arcade.color.LIGHT_BLUE,
                S.font(20),
                anchor_x="center",
                anchor_y="center"
            )
            
            # 根据职业给出建议
            suggestions = self._get_stat_suggestions()
            sugg_y = self.window_height * 0.72
            for stat_name, suggested_value in suggestions.items():
                stat_display_name = self._get_stat_display_name(stat_name)
                current_value = getattr(self.stats, stat_name)
                
                # 高亮推荐的属性
                if current_value >= suggested_value - 2:
                    color = arcade.color.LIGHT_GREEN
                else:
                    color = arcade.color.WHITE
                
                arcade.draw_text(
                    f"{stat_display_name}: {suggested_value}",
                    self.layout_center_x - S.px(200),
                    sugg_y,
                    color,
                    S.font(18),
                    anchor_x="left",
                    anchor_y="center"
                )
                sugg_y -= S.py(30)
        
        # 绘制属性行
        stat_names = ["strength", "dexterity", "intelligence", "charisma"]
        stat_display_names = ["力量", "敏捷", "心智", "魅力"]
        
        for i, (stat_name, display_name) in enumerate(zip(stat_names, stat_display_names)):
            y_pos = self.stat_rows_start_y - i * self.stat_row_height
            current_value = getattr(self.stats, stat_name)
            
            # 属性名称
            arcade.draw_text(
                display_name,
                self.window_width * 0.3,
                y_pos,
                arcade.color.WHITE,
                S.font(28),
                anchor_x="right",
                anchor_y="center",
                bold=True
            )
            
            # 属性值
            arcade.draw_text(
                str(current_value),
                self.layout_center_x,
                y_pos,
                arcade.color.YELLOW,
                S.font(32),
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
            
            # 调整值
            modifier = (current_value - 10) // 2
            mod_text = f"调整值: {modifier:+d}"
            arcade.draw_text(
                mod_text,
                self.window_width * 0.7,
                y_pos,
                arcade.color.LIGHT_GRAY,
                S.font(20),
                anchor_x="left",
                anchor_y="center"
            )
            
            # 增加按钮
            cost = self._get_stat_cost(current_value)
            can_increase = (self.available_points >= cost and current_value < self.max_stat)
            
            btn_color = arcade.color.GREEN if can_increase else arcade.color.DARK_GRAY
            btn_x = self.layout_center_x + S.px(100)
            arcade.draw_lrbt_rectangle_filled(
                btn_x - S.px(20), btn_x + S.px(20),
                y_pos - S.py(20), y_pos + S.py(20),
                btn_color
            )
            arcade.draw_text(
                "+",
                btn_x,
                y_pos,
                arcade.color.WHITE,
                S.font(24),
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
            
            # 减少按钮
            can_decrease = (current_value > self.base_stat)
            btn_color = arcade.color.RED if can_decrease else arcade.color.DARK_GRAY
            btn_x = self.layout_center_x + S.px(160)
            arcade.draw_lrbt_rectangle_filled(
                btn_x - S.px(20), btn_x + S.px(20),
                y_pos - S.py(20), y_pos + S.py(20),
                btn_color
            )
            arcade.draw_text(
                "-",
                btn_x,
                y_pos,
                arcade.color.WHITE,
                S.font(24),
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
            
            # 花费提示
            if current_value < self.max_stat:
                cost_text = f"花费: {cost}"
                arcade.draw_text(
                    cost_text,
                    btn_x + S.px(80),
                    y_pos,
                    arcade.color.ORANGE,
                    S.font(16),
                    anchor_x="left",
                    anchor_y="center"
                )
        
        # 说明文字
        arcade.draw_text(
            "从10点开始，提升属性需要消耗点数（越高越贵），最高16点",
            self.layout_center_x,
            S.py(100),
            arcade.color.GRAY,
            S.font(16),
            anchor_x="center",
            anchor_y="center"
        )
        
        # 上一步和下一步按钮
        # 上一步
        button_x = self.window_width * 0.15
        button_y = S.py(80)
        arcade.draw_lrbt_rectangle_filled(
            button_x - S.px(75), button_x + S.px(75),
            button_y - S.py(25), button_y + S.py(25),
            arcade.color.BLUE
        )
        arcade.draw_text(
            "上一步",
            button_x,
            button_y,
            arcade.color.WHITE,
            S.font(20),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # 下一步
        button_color = arcade.color.GREEN if self.available_points >= 0 else arcade.color.DARK_GRAY
        button_x = self.window_width * 0.85
        button_y = S.py(80)
        arcade.draw_lrbt_rectangle_filled(
            button_x - S.px(75), button_x + S.px(75),
            button_y - S.py(25), button_y + S.py(25),
            button_color
        )
        text_color = arcade.color.WHITE if self.available_points >= 0 else arcade.color.GRAY
        arcade.draw_text(
            "下一步",
            button_x,
            button_y,
            text_color,
            S.font(20),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
    
    def _draw_equipment_selection(self):
        """绘制装备选择界面"""
        # 标题
        arcade.draw_text(
            "选择初始装备",
            self.layout_center_x,
            self.window_height * 0.9,
            arcade.color.GOLD,
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # 装备选项
        equipment_sets = [
            {
                "name": "轻甲 + 刺剑",
                "description": "适合灵活的战斗风格\n提供戳刺和劈砍各两张卡牌\n偏好：敏捷型角色",
                "armor": "布衣",
                "weapon": "手半剑",
                "cards": ["刺击 x2", "劈砍 x2"],
                "preference": "高敏捷"
            },
            {
                "name": "中甲 + 匕首",
                "description": "平衡的防御和攻击\n提供四张戳刺卡牌\n偏好：均衡型角色",
                "armor": "皮甲",
                "weapon": "训练木剑",
                "cards": ["刺击 x4"],
                "preference": "均衡属性"
            },
            {
                "name": "法袍",
                "description": "专注法术的道路\n+1法术卡牌检定加值和伤害\n偏好：高心智角色",
                "armor": "学徒法袍",
                "weapon": "",
                "cards": ["法术加成 +1"],
                "preference": "高心智"
            }
        ]
        
        for i, equip_set in enumerate(equipment_sets):
            y_pos = self.equipment_options_start_y - i * self.equipment_option_height
            is_selected = (i == self.selected_equipment_set)
            is_hovered = (i == self.hovered_equipment_index)
            
            # 背景框
            if is_selected:
                bg_color = arcade.color.DARK_GREEN
            elif is_hovered:
                bg_color = arcade.color.DARK_SLATE_GRAY
            else:
                bg_color = arcade.color.DARK_GRAY
            
            box_width = self.window_width * 0.7
            box_height = S.py(120)
            arcade.draw_lrbt_rectangle_filled(
                self.layout_center_x - box_width / 2,
                self.layout_center_x + box_width / 2,
                y_pos - box_height / 2,
                y_pos + box_height / 2,
                bg_color
            )
            
            # 边框
            border_color = arcade.color.GOLD if is_selected else arcade.color.WHITE
            arcade.draw_lrbt_rectangle_outline(
                self.layout_center_x - box_width / 2,
                self.layout_center_x + box_width / 2,
                y_pos - box_height / 2,
                y_pos + box_height / 2,
                border_color,
                3 if is_selected else 1
            )
            
            # 装备名称
            name_color = arcade.color.YELLOW if is_selected else arcade.color.WHITE
            arcade.draw_text(
                equip_set["name"],
                self.layout_center_x - box_width * 0.35,
                y_pos + S.py(30),
                name_color,
                S.font(24),
                anchor_x="left",
                anchor_y="center",
                bold=True
            )
            
            # 描述
            desc_lines = equip_set["description"].split('\n')
            desc_y = y_pos
            for line in desc_lines:
                arcade.draw_text(
                    line,
                    self.layout_center_x - box_width * 0.35,
                    desc_y,
                    arcade.color.LIGHT_GRAY,
                    S.font(16),
                    anchor_x="left",
                    anchor_y="center"
                )
                desc_y -= S.py(22)
            
            # 偏好
            arcade.draw_text(
                f"偏好: {equip_set['preference']}",
                self.layout_center_x - box_width * 0.35,
                desc_y - S.py(10),
                arcade.color.LIGHT_BLUE,
                S.font(14),
                anchor_x="left",
                anchor_y="center",
                italic=True
            )
            
            # 背包预览（右侧）
            preview_x = self.layout_center_x + box_width * 0.1
            preview_y = y_pos
            
            arcade.draw_text(
                "背包预览:",
                preview_x,
                preview_y + S.py(40),
                arcade.color.GREEN,
                S.font(18),
                anchor_x="left",
                anchor_y="center",
                bold=True
            )
            
            # 显示装备
            item_y = preview_y + S.py(10)
            if equip_set["armor"]:
                arcade.draw_text(
                    f"🛡️ {equip_set['armor']}",
                    preview_x,
                    item_y,
                    arcade.color.WHITE,
                    S.font(16),
                    anchor_x="left",
                    anchor_y="center"
                )
                item_y -= S.py(25)
            
            if equip_set["weapon"]:
                arcade.draw_text(
                    f"⚔️ {equip_set['weapon']}",
                    preview_x,
                    item_y,
                    arcade.color.WHITE,
                    S.font(16),
                    anchor_x="left",
                    anchor_y="center"
                )
                item_y -= S.py(25)
            
            # 显示卡牌
            for card in equip_set["cards"]:
                arcade.draw_text(
                    f"🃏 {card}",
                    preview_x,
                    item_y,
                    arcade.color.CYAN,
                    S.font(16),
                    anchor_x="left",
                    anchor_y="center"
                )
                item_y -= S.py(22)
        
        # 说明文字
        arcade.draw_text(
            "点击装备套装进行选择，然后点击右下角的'开始游戏'",
            self.layout_center_x,
            S.py(50),
            arcade.color.GRAY,
            S.font(16),
            anchor_x="center",
            anchor_y="center"
        )
        
        # 上一步和开始游戏按钮
        # 上一步
        button_x = self.window_width * 0.15
        button_y = S.py(80)
        arcade.draw_lrbt_rectangle_filled(
            button_x - S.px(75), button_x + S.px(75),
            button_y - S.py(25), button_y + S.py(25),
            arcade.color.BLUE
        )
        arcade.draw_text(
            "上一步",
            button_x,
            button_y,
            arcade.color.WHITE,
            S.font(20),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # 开始游戏
        button_x = self.window_width * 0.85
        button_y = S.py(80)
        arcade.draw_lrbt_rectangle_filled(
            button_x - S.px(75), button_x + S.px(75),
            button_y - S.py(25), button_y + S.py(25),
            arcade.color.GREEN
        )
        arcade.draw_text(
            "开始游戏",
            button_x,
            button_y,
            arcade.color.WHITE,
            S.font(20),
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
    
    def _get_stat_cost(self, current_value: int) -> int:
        """获取提升属性的花费（DND 18点购买规则）"""
        # 18点购买系统的成本表
        cost_table = {
            10: 0,
            11: 1,
            12: 2,
            13: 3,
            14: 5,
            15: 7,
            16: 10
        }
        
        if current_value >= self.max_stat:
            return 999  # 无法再提升
        
        next_value = current_value + 1
        if next_value in cost_table:
            return cost_table[next_value] - cost_table.get(current_value, 0)
        
        return 999
    
    def _get_stat_suggestions(self) -> Dict[str, int]:
        """根据职业获取属性建议"""
        if not self.selected_career:
            return {}
        
        # 根据职业类型给出建议
        suggestions = {
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "charisma": 10
        }
        
        career_type = self.selected_career.career_type
        
        if career_type == CareerType.DRIFTER:
            # 流浪者：敏捷优先
            suggestions["dexterity"] = 14
            suggestions["strength"] = 12
        elif career_type == CareerType.ARTISAN:
            # 手艺人：力量和敏捷均衡
            suggestions["strength"] = 13
            suggestions["dexterity"] = 13
        elif career_type == CareerType.PEDLAR:
            # 行商：魅力优先
            suggestions["charisma"] = 15
            suggestions["intelligence"] = 12
        elif career_type == CareerType.FARMER:
            # 农民：力量和心智
            suggestions["strength"] = 14
            suggestions["intelligence"] = 12
        elif career_type == CareerType.SCHOLAR:
            # 学者：心智优先
            suggestions["intelligence"] = 15
            suggestions["charisma"] = 12
        
        return suggestions
    
    def _get_stat_display_name(self, stat_name: str) -> str:
        """获取属性的显示名称"""
        names = {
            "strength": "力量",
            "dexterity": "敏捷",
            "intelligence": "心智",
            "charisma": "魅力",
            "luck": "幸运"
        }
        return names.get(stat_name, stat_name)
    
    def _wrap_text(self, text: str, max_chars: int) -> List[str]:
        """文本换行"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """鼠标移动事件"""
        if self.creation_stage == 0:
            # 职业选择阶段的悬停检测
            careers = CareerFactory.get_all_careers()
            self.hovered_career_index = -1
            
            for i, career in enumerate(careers):
                y_pos = self.career_list_y_start - i * self.career_item_height
                if (abs(x - self.career_list_x) < S.px(150) and 
                    abs(y - y_pos) < S.py(25)):
                    self.hovered_career_index = i
                    break
        
        elif self.creation_stage == 2:
            # 装备选择阶段的悬停检测
            self.hovered_equipment_index = -1
            
            for i in range(3):
                y_pos = self.equipment_options_start_y - i * self.equipment_option_height
                box_width = self.window_width * 0.7
                box_height = S.py(120)
                
                if (abs(x - self.layout_center_x) < box_width / 2 and 
                    abs(y - y_pos) < box_height / 2):
                    self.hovered_equipment_index = i
                    break
    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """鼠标点击事件"""
        if self.creation_stage == 0:
            self._handle_career_selection_click(x, y)
        elif self.creation_stage == 1:
            self._handle_stat_allocation_click(x, y)
        elif self.creation_stage == 2:
            self._handle_equipment_selection_click(x, y)
    
    def _handle_career_selection_click(self, x: float, y: float):
        """处理职业选择界面的点击"""
        # 检查是否点击了职业
        careers = CareerFactory.get_all_careers()
        for i, career in enumerate(careers):
            y_pos = self.career_list_y_start - i * self.career_item_height
            if (abs(x - self.career_list_x) < S.px(150) and 
                abs(y - y_pos) < S.py(25)):
                self.selected_career = career
                return
        
        # 检查是否点击了下一步按钮
        button_x = self.window_width * 0.85
        button_y = S.py(80)
        if (abs(x - button_x) < S.px(75) and abs(y - button_y) < S.py(25)):
            if self.selected_career:
                self.creation_stage = 1
    
    def _handle_stat_allocation_click(self, x: float, y: float):
        """处理属性分配界面的点击"""
        stat_names = ["strength", "dexterity", "intelligence", "charisma"]
        
        for i, stat_name in enumerate(stat_names):
            y_pos = self.stat_rows_start_y - i * self.stat_row_height
            current_value = getattr(self.stats, stat_name)
            
            # 检查增加按钮
            btn_x = self.layout_center_x + S.px(100)
            if (abs(x - btn_x) < S.px(20) and abs(y - y_pos) < S.py(20)):
                cost = self._get_stat_cost(current_value)
                if self.available_points >= cost and current_value < self.max_stat:
                    setattr(self.stats, stat_name, current_value + 1)
                    self.available_points -= cost
                return
            
            # 检查减少按钮
            btn_x = self.layout_center_x + S.px(160)
            if (abs(x - btn_x) < S.px(20) and abs(y - y_pos) < S.py(20)):
                if current_value > self.base_stat:
                    # 返还点数
                    prev_value = current_value - 1
                    cost = self._get_stat_cost(prev_value)
                    setattr(self.stats, stat_name, prev_value)
                    self.available_points += cost
                return
        
        # 检查上一步按钮
        button_x = self.window_width * 0.15
        button_y = S.py(80)
        if (abs(x - button_x) < S.px(75) and abs(y - button_y) < S.py(25)):
            self.creation_stage = 0
            return
        
        # 检查下一步按钮
        button_x = self.window_width * 0.85
        button_y = S.py(80)
        if (abs(x - button_x) < S.px(75) and abs(y - button_y) < S.py(25)):
            if self.available_points >= 0:
                self.creation_stage = 2
    
    def _handle_equipment_selection_click(self, x: float, y: float):
        """处理装备选择界面的点击"""
        # 检查是否点击了装备选项
        for i in range(3):
            y_pos = self.equipment_options_start_y - i * self.equipment_option_height
            box_width = self.window_width * 0.7
            box_height = S.py(120)
                        
            if (abs(x - self.layout_center_x) < box_width / 2 and
                abs(y - y_pos) < box_height / 2):
                self.selected_equipment_set = i
                return
        
        # 检查上一步按钮
        button_x = self.window_width * 0.15
        button_y = S.py(80)
        if (abs(x - button_x) < S.px(75) and abs(y - button_y) < S.py(25)):
            self.creation_stage = 1
            return
        
        # 检查开始游戏按钮
        button_x = self.window_width * 0.85
        button_y = S.py(80)
        if (abs(x - button_x) < S.px(75) and abs(y - button_y) < S.py(25)):
            self._create_character_and_start()
    
    def _create_character_and_start(self):
        """创建角色并开始游戏"""
        # 根据选择的装备套装创建装备
        weapons_db = create_weapon_database()
        armors_db = create_armor_database()
        
        equipment = {}
        cards_for_deck = []
        
        if self.selected_equipment_set == 0:
            # 轻甲 + 刺剑（手半剑）
            equipment["armor"] = armors_db.get("cloth")
            equipment["weapon"] = weapons_db.get("bastard_sword")
            # 手半剑已经提供了刺击和劈砍卡牌
        elif self.selected_equipment_set == 1:
            # 中甲 + 匕首（训练木剑作为替代）
            equipment["armor"] = armors_db.get("leather")
            equipment["weapon"] = weapons_db.get("wooden_sword")
        elif self.selected_equipment_set == 2:
            # 法袍
            equipment["armor"] = armors_db.get("apprentice_robe")
            # 法师没有武器，或者可以添加一个魔法杖
            # equipment["weapon"] = weapons_db.get("magic_staff")
        
        # 创建实体 - 使用职业专属卡组
        from card_database import create_card_database, get_career_deck
        cards_db = create_card_database()
        
        # 获取职业专属卡组
        if self.selected_career:
            deck = get_career_deck(self.selected_career.career_type)
        else:
            # 默认卡组
            deck = []
            for card_name in ["刺击", "劈砍", "格挡", "治疗"]:
                if card_name in cards_db:
                    deck.append(cards_db[card_name].copy())
        
        # 常驻卡牌（不参与抽牌，每回合自动在手牌中）
        permanent_cards = []
        if "基础移动" in cards_db:
            permanent_cards.append(cards_db["基础移动"].copy())
        
        # 创建玩家实体
        player = Entity(
            name=self.character_name,
            max_hp=10,  # 初始血量为10（与预设角色一致）
            max_ap=3,
            equipment=equipment,
            cards=deck,  # 使用职业专属卡组
            hand_size=4,
            stats=self.stats,
            control_type=ControlType.PLAYER,
            position=(2, 7),
            permanent_cards=permanent_cards  # 传入常驻卡牌（基础移动）
        )
        
        # 设置职业
        player.career = self.selected_career
        
        # 将初始装备同步到 equipment_manager（用于装备界面显示）
        from inventory import InventoryItem, ItemType
        from equipment_manager import EquipmentSlot
        
        if "weapon" in equipment and equipment["weapon"]:
            weapon = equipment["weapon"]
            # 创建对应的 InventoryItem
            weapon_item = InventoryItem(
                name=weapon.name,
                item_type=ItemType.WEAPON,
                description=weapon.description,
                weight=1.0,
                volume=1,
                icon_color=(255, 165, 0)  # 橙色
            )
            # 装备到武器槽位
            player.equipment_manager.equip_item(weapon_item, EquipmentSlot.WEAPON)
        
        if "armor" in equipment and equipment["armor"]:
            armor = equipment["armor"]
            # 创建对应的 InventoryItem
            armor_item = InventoryItem(
                name=armor.name,
                item_type=ItemType.ARMOR,
                description=armor.description,
                weight=2.0,
                volume=2,
                icon_color=(100, 149, 237)  # 蓝色
            )
            # 装备到躯干槽位
            player.equipment_manager.equip_item(armor_item, EquipmentSlot.BODY)
        
        # 调用回调函数，传递创建好的角色
        self.on_character_created(player)
    
    def on_key_press(self, key: int, modifiers: int):
        """键盘按键事件"""
        if key == arcade.key.ESCAPE:
            # ESC键返回上一阶段或关闭窗口
            if self.creation_stage > 0:
                self.creation_stage -= 1
            else:
                arcade.close_window()

"""
装备和属性UI渲染器模块
负责绘制装备界面、角色属性和可装备物品列表
"""
import arcade
from typing import Optional, Tuple, Dict
from equipment_manager import EquipmentManager, EquipmentSlot
from inventory import Inventory, InventoryItem, ItemType
from models import Stats
from config import CONSTANTS


class EquipmentRenderer:
    """装备和属性UI渲染器"""
    
    def __init__(self, window_width: int, window_height: int):
        self.window_width = window_width
        self.window_height = window_height
        
        # 显示状态
        self.visible = False
        self.current_entity = None
        
        # 鼠标交互
        self.hovered_slot: Optional[EquipmentSlot] = None
        self.hovered_inventory_item: Optional[Tuple[int, int]] = None  # (grid_x, grid_y)
        
        # 计算面板位置（右侧显示）
        self._calculate_panel_position()
    
    def _calculate_panel_position(self):
        """计算装备面板的位置"""
        # 面板尺寸
        self.panel_width = 400
        self.panel_height = 600
        
        # 靠右显示，留出边距
        self.panel_x = self.window_width - self.panel_width - 20
        self.panel_y = (self.window_height - self.panel_height) // 2
        
        # 分区高度
        self.stats_section_height = 150      # 属性区
        self.equipment_section_height = 200  # 装备区
        self.inventory_section_height = 250  # 背包物品区
    
    def toggle_visibility(self, entity):
        """切换装备界面显示"""
        self.current_entity = entity
        self.visible = not self.visible
        
        if self.visible:
            self._calculate_panel_position()
    
    def close(self):
        """关闭装备界面"""
        self.visible = False
        self.hovered_slot = None
        self.hovered_inventory_item = None
    
    def is_visible(self) -> bool:
        """检查是否可见"""
        return self.visible
    
    def draw(self):
        """绘制装备界面"""
        if not self.visible or not self.current_entity:
            return
        
        self._draw_background()
        self._draw_title()
        self._draw_stats_section()
        self._draw_equipment_section()
        self._draw_inventory_section()
        self._draw_hover_tooltip()
    
    def _draw_background(self):
        """绘制背景"""
        left = self.panel_x
        right = self.panel_x + self.panel_width
        bottom = self.panel_y
        top = self.panel_y + self.panel_height
        
        # 半透明背景
        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top,
            (0, 0, 0, 220)
        )
        
        # 边框
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top,
            arcade.color.WHITE,
            border_width=3
        )
    
    def _draw_title(self):
        """绘制标题"""
        title_text = f"装备与属性 - {self.current_entity.name}"
        arcade.draw_text(
            title_text,
            self.panel_x + 15,
            self.panel_y + self.panel_height - 30,
            arcade.color.WHITE,
            font_size=18,
            bold=True
        )
    
    def _draw_stats_section(self):
        """绘制属性区域"""
        section_y = self.panel_y + self.panel_height - 70
        
        # 标题
        arcade.draw_text(
            "角色属性",
            self.panel_x + 15,
            section_y,
            arcade.color.YELLOW,
            font_size=14,
            bold=True
        )
        
        # 属性列表
        stats = self.current_entity.stats
        stat_y = section_y - 30
        stats_data = [
            ("力量 (STR)", stats.strength),
            ("敏捷 (DEX)", stats.dexterity),
            ("心智 (INT)", stats.intelligence),
            ("魅力 (CHA)", stats.charisma),
            ("幸运 (LUK)", stats.luck),
        ]
        
        for label, value in stats_data:
            text = f"{label}: {value}"
            arcade.draw_text(
                text,
                self.panel_x + 20,
                stat_y,
                arcade.color.WHITE,
                font_size=12
            )
            stat_y -= 25
        
        # HP和AP
        hp_ap_y = stat_y - 10
        arcade.draw_text(
            f"HP: {self.current_entity.hp}/{self.current_entity.max_hp}",
            self.panel_x + 20,
            hp_ap_y,
            arcade.color.RED,
            font_size=12,
            bold=True
        )
        
        arcade.draw_text(
            f"AP: {self.current_entity.ap}/{self.current_entity.max_ap}",
            self.panel_x + 200,
            hp_ap_y,
            arcade.color.BLUE,
            font_size=12,
            bold=True
        )
    
    def _draw_equipment_section(self):
        """绘制装备区域"""
        section_top = self.panel_y + self.panel_height - 70 - self.stats_section_height
        
        # 标题
        arcade.draw_text(
            "当前装备",
            self.panel_x + 15,
            section_top,
            arcade.color.YELLOW,
            font_size=14,
            bold=True
        )
        
        # 获取装备管理器
        equip_mgr = self.current_entity.equipment_manager
        
        # 绘制槽位
        slot_y = section_top - 40
        slot_index = 0
        
        for slot in equip_mgr.unlocked_slots:
            item = equip_mgr.get_equipped_item(slot)
            
            # 槽位名称
            slot_name_map = {
                EquipmentSlot.BODY: "全身装备",
                EquipmentSlot.WEAPON: "武器",
            }
            slot_name = slot_name_map.get(slot, slot.value)
            
            # 槽位背景
            slot_left = self.panel_x + 15
            slot_right = self.panel_x + 185
            slot_bottom = slot_y - 35
            slot_top = slot_y
            
            # 高亮悬停槽位
            if self.hovered_slot == slot:
                bg_color = (100, 100, 100, 200)
            else:
                bg_color = (50, 50, 50, 200)
            
            arcade.draw_lrbt_rectangle_filled(
                slot_left, slot_right, slot_bottom, slot_top,
                bg_color
            )
            arcade.draw_lrbt_rectangle_outline(
                slot_left, slot_right, slot_bottom, slot_top,
                arcade.color.GRAY,
                border_width=2
            )
            
            # 槽位标签
            arcade.draw_text(
                slot_name,
                slot_left + 5,
                slot_top - 12,
                arcade.color.LIGHT_GRAY,
                font_size=10
            )
            
            # 装备物品
            if item:
                arcade.draw_text(
                    item.name,
                    slot_left + 5,
                    slot_bottom + 8,
                    arcade.color.WHITE,
                    font_size=11,
                    bold=True
                )
                
                # 物品类型标签
                type_color = {
                    ItemType.WEAPON: arcade.color.ORANGE,
                    ItemType.ARMOR: arcade.color.BLUE,
                }.get(item.item_type, arcade.color.WHITE)
                
                arcade.draw_text(
                    f"[{item.item_type.value}]",
                    slot_left + 5,
                    slot_bottom + 2,
                    type_color,
                    font_size=9
                )
            else:
                arcade.draw_text(
                    "<空>",
                    slot_left + 5,
                    slot_bottom + 8,
                    arcade.color.DARK_GRAY,
                    font_size=11
                )
            
            slot_y -= 50
            slot_index += 1
    
    def _draw_inventory_section(self):
        """绘制背包物品区域（可装备的物品）"""
        section_top = self.panel_y + self.panel_height - 70 - self.stats_section_height - self.equipment_section_height
        
        # 标题
        arcade.draw_text(
            "背包中的装备",
            self.panel_x + 15,
            section_top,
            arcade.color.YELLOW,
            font_size=14,
            bold=True
        )
        
        # 获取可装备的物品
        if hasattr(self.current_entity, 'inventory'):
            inventory = self.current_entity.inventory
            equippable_items = []
            
            for item in inventory.items:
                if item.item_type in [ItemType.WEAPON, ItemType.ARMOR]:
                    equippable_items.append(item)
            
            # 绘制物品列表
            item_y = section_top - 30
            max_display = 6  # 最多显示6个物品
            
            for i, item in enumerate(equippable_items[:max_display]):
                if item_y < self.panel_y + 20:
                    break
                
                # 物品背景
                item_left = self.panel_x + 15
                item_right = self.panel_x + self.panel_width - 15
                item_bottom = item_y - 25
                item_top = item_y
                
                # 高亮悬停物品
                if self.hovered_inventory_item and self.hovered_inventory_item[1] == i:
                    bg_color = (80, 80, 80, 200)
                else:
                    bg_color = (40, 40, 40, 200)
                
                arcade.draw_lrbt_rectangle_filled(
                    item_left, item_right, item_bottom, item_top,
                    bg_color
                )
                arcade.draw_lrbt_rectangle_outline(
                    item_left, item_right, item_bottom, item_top,
                    arcade.color.GRAY,
                    border_width=1
                )
                
                # 物品名称
                color_map = {
                    ItemType.WEAPON: arcade.color.ORANGE,
                    ItemType.ARMOR: arcade.color.BLUE,
                }
                item_color = color_map.get(item.item_type, arcade.color.WHITE)
                
                arcade.draw_text(
                    item.name,
                    item_left + 5,
                    item_top - 12,
                    item_color,
                    font_size=11,
                    bold=True
                )
                
                # 物品描述
                if item.description:
                    desc_text = item.description[:25] + "..." if len(item.description) > 25 else item.description
                    arcade.draw_text(
                        desc_text,
                        item_left + 5,
                        item_bottom + 3,
                        arcade.color.LIGHT_GRAY,
                        font_size=9
                    )
                
                item_y -= 30
            
            if not equippable_items:
                arcade.draw_text(
                    "没有可装备的物品",
                    self.panel_x + 15,
                    section_top - 50,
                    arcade.color.DARK_GRAY,
                    font_size=12
                )
    
    def _draw_hover_tooltip(self):
        """绘制悬停提示"""
        # TODO: 实现详细的悬停提示
        pass
    
    def get_slot_at_pos(self, mouse_x: float, mouse_y: float) -> Optional[EquipmentSlot]:
        """根据鼠标位置获取装备槽位"""
        if not self.visible or not self.current_entity:
            return None
        
        equip_mgr = self.current_entity.equipment_manager
        section_top = self.panel_y + self.panel_height - 70 - self.stats_section_height
        
        slot_y = section_top - 40
        
        for slot in equip_mgr.unlocked_slots:
            slot_left = self.panel_x + 15
            slot_right = self.panel_x + 185
            slot_bottom = slot_y - 35
            slot_top = slot_y
            
            if (slot_left <= mouse_x <= slot_right and 
                slot_bottom <= mouse_y <= slot_top):
                return slot
            
            slot_y -= 50
        
        return None
    
    def get_inventory_item_at_pos(self, mouse_x: float, mouse_y: float) -> Optional[int]:
        """根据鼠标位置获取背包物品索引"""
        if not self.visible or not self.current_entity:
            return None
        
        if not hasattr(self.current_entity, 'inventory'):
            return None
        
        inventory = self.current_entity.inventory
        equippable_items = [
            item for item in inventory.items 
            if item.item_type in [ItemType.WEAPON, ItemType.ARMOR]
        ]
        
        section_top = self.panel_y + self.panel_height - 70 - self.stats_section_height - self.equipment_section_height
        item_y = section_top - 30
        
        for i, item in enumerate(equippable_items[:6]):
            item_left = self.panel_x + 15
            item_right = self.panel_x + self.panel_width - 15
            item_bottom = item_y - 25
            item_top = item_y
            
            if (item_left <= mouse_x <= item_right and 
                item_bottom <= mouse_y <= item_top):
                return i
            
            item_y -= 30
        
        return None
    
    def update_hover(self, mouse_x: float, mouse_y: float):
        """更新悬停状态"""
        if not self.visible:
            self.hovered_slot = None
            self.hovered_inventory_item = None
            return
        
        # 检查装备槽位
        self.hovered_slot = self.get_slot_at_pos(mouse_x, mouse_y)
        
        # 检查背包物品
        item_index = self.get_inventory_item_at_pos(mouse_x, mouse_y)
        if item_index is not None:
            self.hovered_inventory_item = (mouse_x, item_index)
        else:
            self.hovered_inventory_item = None

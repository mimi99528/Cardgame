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
from ui_scale import S


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
        
        # 拖动状态
        self.dragged_item: Optional[InventoryItem] = None  # 正在拖动的物品
        self.drag_source: Optional[str] = None  # 拖动来源: 'slot' 或 'inventory'
        self.drag_source_slot: Optional[EquipmentSlot] = None  # 如果是从槽位拖动，记录槽位
        self.drag_start_pos: Optional[Tuple[float, float]] = None  # 拖动起始位置
        self.drag_current_pos: Optional[Tuple[float, float]] = None  # 拖动当前位置
        
        # 计算面板位置（右侧显示）
        self._calculate_panel_position()
    
    def _calculate_panel_position(self):
        """计算装备面板的位置"""
        # 面板尺寸（按缩放比例换算）
        self.panel_width = S.px(400)
        self.panel_height = S.py(600)
        
        # 靠右显示，留出边距
        self.panel_x = self.window_width - self.panel_width - S.px(20)
        self.panel_y = (self.window_height - self.panel_height) // 2
        
        # 分区高度
        self.stats_section_height = S.py(150)      # 属性区
        self.equipment_section_height = S.py(220)  # 装备区（增加高度以容纳格子布局）
        self.inventory_section_height = S.py(230)  # 背包物品区
        
        # 装备格子配置
        self.slot_size = S.scale(80)   # 每个装备格子的大小
        self.slot_padding = S.px(15)   # 格子间距
        self.equipment_grid_start_x = self.panel_x + S.px(30)  # 装备网格起始X
        self.equipment_grid_start_y = (self.panel_y + self.panel_height
                                       - S.py(70) - self.stats_section_height - S.py(40))
    
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
        # 清除拖动状态
        self.dragged_item = None
        self.drag_source = None
        self.drag_source_slot = None
        self.drag_start_pos = None
        self.drag_current_pos = None
    
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
        
        # 绘制拖动的物品（最后绘制，确保在最上层）
        self.draw_dragged_item()
    
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
            font_size=S.font(18),
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
            font_size=S.font(14),
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
                font_size=S.font(12)
            )
            stat_y -= 25
        
        # HP和AP
        hp_ap_y = stat_y - 10
        arcade.draw_text(
            f"HP: {self.current_entity.hp}/{self.current_entity.max_hp}",
            self.panel_x + 20,
            hp_ap_y,
            arcade.color.RED,
            font_size=S.font(12),
            bold=True
        )
        
        arcade.draw_text(
            f"AP: {self.current_entity.ap}/{self.current_entity.max_ap}",
            self.panel_x + 200,
            hp_ap_y,
            arcade.color.BLUE,
            font_size=S.font(12),
            bold=True
        )
    
    def _draw_equipment_section(self):
        """绘制装备区域（方形格子布局）"""
        section_top = self.panel_y + self.panel_height - 70 - self.stats_section_height
        
        # 标题
        arcade.draw_text(
            "当前装备",
            self.panel_x + 15,
            section_top,
            arcade.color.YELLOW,
            font_size=S.font(14),
            bold=True
        )
        
        # 获取装备管理器
        equip_mgr = self.current_entity.equipment_manager
        
        # 定义槽位布局（反映真实位置）
        # 躯干在中间，武器在右下，饰品在左下
        slot_positions = {
            EquipmentSlot.BODY: (self.equipment_grid_start_x + self.slot_size + self.slot_padding, 
                                self.equipment_grid_start_y),  # 中间
            EquipmentSlot.WEAPON: (self.equipment_grid_start_x + (self.slot_size + self.slot_padding) * 2,
                                  self.equipment_grid_start_y - self.slot_size - self.slot_padding),  # 右下
            EquipmentSlot.ACCESSORY: (self.equipment_grid_start_x,
                                     self.equipment_grid_start_y - self.slot_size - self.slot_padding),  # 左下
        }
        
        # 槽位名称映射
        slot_name_map = {
            EquipmentSlot.BODY: "躯干",
            EquipmentSlot.WEAPON: "武器",
            EquipmentSlot.ACCESSORY: "饰品",
        }
        
        # 绘制每个槽位
        for slot, (slot_x, slot_y) in slot_positions.items():
            if slot not in equip_mgr.unlocked_slots:
                continue
            
            item = equip_mgr.get_equipped_item(slot)
            
            # 槽位背景
            slot_left = slot_x
            slot_right = slot_x + self.slot_size
            slot_bottom = slot_y - self.slot_size
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
            
            # 槽位标签（顶部）
            slot_name = slot_name_map.get(slot, slot.value)
            arcade.draw_text(
                slot_name,
                slot_left + self.slot_size // 2,
                slot_top - 12,
                arcade.color.LIGHT_GRAY,
                font_size=S.font(10),
                anchor_x="center"
            )
            
            # 装备物品
            if item:
                # 物品名称（居中显示）
                arcade.draw_text(
                    item.name,
                    slot_left + self.slot_size // 2,
                    slot_top - self.slot_size // 2 + 5,
                    arcade.color.WHITE,
                    font_size=S.font(11),
                    bold=True,
                    anchor_x="center",
                    anchor_y="center",
                    width=self.slot_size - 10,
                    align="center"
                )
                
                # 物品类型标签（底部）
                type_color = {
                    ItemType.WEAPON: arcade.color.ORANGE,
                    ItemType.ARMOR: arcade.color.BLUE,
                    ItemType.ACCESSORY: arcade.color.PURPLE,
                }.get(item.item_type, arcade.color.WHITE)
                
                arcade.draw_text(
                    f"[{item.item_type.value}]",
                    slot_left + self.slot_size // 2,
                    slot_bottom + 12,
                    type_color,
                    font_size=S.font(9),
                    anchor_x="center"
                )
            else:
                arcade.draw_text(
                    "<空>",
                    slot_left + self.slot_size // 2,
                    slot_top - self.slot_size // 2,
                    arcade.color.DARK_GRAY,
                    font_size=S.font(11),
                    anchor_x="center",
                    anchor_y="center"
                )
    
    def _draw_inventory_section(self):
        """绘制背包物品区域（可装备的物品）"""
        section_top = self.panel_y + self.panel_height - 70 - self.stats_section_height - self.equipment_section_height
        
        # 标题
        arcade.draw_text(
            "背包中的装备",
            self.panel_x + 15,
            section_top,
            arcade.color.YELLOW,
            font_size=S.font(14),
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
                    ItemType.ACCESSORY: arcade.color.PURPLE,
                }
                item_color = color_map.get(item.item_type, arcade.color.WHITE)
                
                arcade.draw_text(
                    item.name,
                    item_left + 5,
                    item_top - 12,
                    item_color,
                    font_size=S.font(11),
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
                        font_size=S.font(9)
                    )
                
                item_y -= 30
            
            if not equippable_items:
                arcade.draw_text(
                    "没有可装备的物品",
                    self.panel_x + 15,
                    section_top - 50,
                    arcade.color.DARK_GRAY,
                    font_size=S.font(12)
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
        
        # 定义槽位布局（与绘制时一致）
        slot_positions = {
            EquipmentSlot.BODY: (self.equipment_grid_start_x + self.slot_size + self.slot_padding, 
                                self.equipment_grid_start_y),  # 中间
            EquipmentSlot.WEAPON: (self.equipment_grid_start_x + (self.slot_size + self.slot_padding) * 2,
                                  self.equipment_grid_start_y - self.slot_size - self.slot_padding),  # 右下
            EquipmentSlot.ACCESSORY: (self.equipment_grid_start_x,
                                     self.equipment_grid_start_y - self.slot_size - self.slot_padding),  # 左下
        }
        
        for slot, (slot_x, slot_y) in slot_positions.items():
            if slot not in equip_mgr.unlocked_slots:
                continue
            
            slot_left = slot_x
            slot_right = slot_x + self.slot_size
            slot_bottom = slot_y - self.slot_size
            slot_top = slot_y
            
            if (slot_left <= mouse_x <= slot_right and 
                slot_bottom <= mouse_y <= slot_top):
                return slot
        
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
            if item.item_type in [ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY]
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
    
    def start_drag_from_slot(self, slot: EquipmentSlot, mouse_x: float, mouse_y: float) -> bool:
        """
        开始从槽位拖动装备
        
        Args:
            slot: 装备槽位
            mouse_x, mouse_y: 鼠标位置
            
        Returns:
            是否成功开始拖动
        """
        if not self.visible or not self.current_entity:
            return False
        
        equip_mgr = self.current_entity.equipment_manager
        item = equip_mgr.get_equipped_item(slot)
        
        if item is None:
            return False
        
        self.dragged_item = item
        self.drag_source = 'slot'
        self.drag_source_slot = slot
        self.drag_start_pos = (mouse_x, mouse_y)
        self.drag_current_pos = (mouse_x, mouse_y)
        
        return True
    
    def start_drag_from_inventory(self, item_index: int, mouse_x: float, mouse_y: float) -> bool:
        """
        开始从背包拖动物品
        
        Args:
            item_index: 背包物品索引
            mouse_x, mouse_y: 鼠标位置
            
        Returns:
            是否成功开始拖动
        """
        print(f"start_drag_from_inventory called: item_index={item_index}, visible={self.visible}, entity={self.current_entity is not None}")
        
        if not self.visible or not self.current_entity:
            print("  -> 返回False: 不可见或没有实体")
            return False
        
        if not hasattr(self.current_entity, 'inventory'):
            print("  -> 返回False: 没有背包")
            return False
        
        inventory = self.current_entity.inventory
        equippable_items = [
            item for item in inventory.items 
            if item.item_type in [ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY]
        ]
        
        print(f"  -> equippable_items count: {len(equippable_items)}, item_index: {item_index}")
        
        if 0 <= item_index < len(equippable_items):
            self.dragged_item = equippable_items[item_index]
            self.drag_source = 'inventory'
            self.drag_source_slot = None
            self.drag_start_pos = (mouse_x, mouse_y)
            self.drag_current_pos = (mouse_x, mouse_y)
            print(f"  -> 成功设置dragged_item: {self.dragged_item.name}")
            return True
        
        print("  -> 返回False: item_index超出范围")
        return False
    
    def update_drag(self, mouse_x: float, mouse_y: float):
        """更新拖动位置"""
        print(f"更新拖动位置: {mouse_x}, {mouse_y}", self.dragged_item)
        if self.dragged_item:
            self.drag_current_pos = (mouse_x, mouse_y)
            # 调试输出
            print(f"更新拖动位置: {mouse_x}, {mouse_y}")
    
    def end_drag(self, target_slot: Optional[EquipmentSlot] = None) -> Tuple[bool, str]:
        """
        结束拖动
        
        Args:
            target_slot: 目标槽位（如果拖动到槽位）
            
        Returns:
            (是否成功, 消息)
        """
        if not self.dragged_item:
            return False, "没有拖动的物品"
        
        success = False
        message = ""
        
        try:
            if self.drag_source == 'slot' and target_slot:
                # 从槽位拖动到另一个槽位
                success, message = self._handle_slot_to_slot_drag(target_slot)
            elif self.drag_source == 'inventory' and target_slot:
                # 从背包拖动到槽位
                success, message = self._handle_inventory_to_slot_drag(target_slot)
            elif self.drag_source == 'slot' and not target_slot:
                # 从槽位拖动到空白处（卸下）
                success, message = self._handle_unequip()
            elif self.drag_source == 'inventory' and not target_slot:
                # 从背包拖动到空白处（取消操作）
                success = True
                message = "已取消装备"
            else:
                message = "无效的拖动操作"
        finally:
            # 清除拖动状态
            self.dragged_item = None
            self.drag_source = None
            self.drag_source_slot = None
            self.drag_start_pos = None
            self.drag_current_pos = None
        
        return success, message
    
    def _handle_slot_to_slot_drag(self, target_slot: EquipmentSlot) -> Tuple[bool, str]:
        """处理从槽位到槽位的拖动"""
        if not self.current_entity:
            return False, "没有当前实体"
        
        equip_mgr = self.current_entity.equipment_manager
        source_slot = self.drag_source_slot
        
        if source_slot == target_slot:
            return False, "不能拖动到同一个槽位"
        
        # 获取源物品和目标物品
        source_item = equip_mgr.get_equipped_item(source_slot)
        target_item = equip_mgr.get_equipped_item(target_slot)
        
        # 检查是否可以交换
        if source_item:
            can_equip, reason = equip_mgr.can_equip(source_item, target_slot, self.current_entity)
            if not can_equip:
                return False, reason
        
        # 执行交换
        if target_item:
            # 交换两个槽位的物品
            equip_mgr.equipped_items[source_slot] = target_item
            equip_mgr.equipped_items[target_slot] = source_item
            return True, f"已交换 {source_slot.value} 和 {target_slot.value} 的装备"
        else:
            # 移动到空槽位
            equip_mgr.equipped_items[source_slot] = None
            equip_mgr.equipped_items[target_slot] = source_item
            return True, f"已将装备从 {source_slot.value} 移动到 {target_slot.value}"
    
    def _handle_inventory_to_slot_drag(self, target_slot: EquipmentSlot) -> Tuple[bool, str]:
        """处理从背包到槽位的拖动"""
        if not self.current_entity or not hasattr(self.current_entity, 'inventory'):
            return False, "没有背包"
        
        equip_mgr = self.current_entity.equipment_manager
        inventory = self.current_entity.inventory
        
        # 检查是否可以装备
        can_equip, reason = equip_mgr.can_equip(self.dragged_item, target_slot, self.current_entity)
        if not can_equip:
            return False, reason
        
        # 获取目标槽位的旧物品
        old_item = equip_mgr.get_equipped_item(target_slot)
        
        # 装备新物品
        equip_mgr.equipped_items[target_slot] = self.dragged_item
        
        # 从背包中移除物品
        inventory.remove_item(self.dragged_item)
        
        # 如果有旧物品，放回背包
        if old_item:
            inventory.add_item(old_item)
            return True, f"已装备 {self.dragged_item.name}，{old_item.name} 已放回背包"
        else:
            return True, f"已装备 {self.dragged_item.name}"
    
    def _handle_unequip(self) -> Tuple[bool, str]:
        """处理卸下装备"""
        if not self.current_entity or not hasattr(self.current_entity, 'inventory'):
            return False, "没有背包"
        
        equip_mgr = self.current_entity.equipment_manager
        inventory = self.current_entity.inventory
        source_slot = self.drag_source_slot
        
        # 卸下装备
        success, message, old_item = equip_mgr.unequip_item(source_slot)
        
        if success and old_item:
            # 将卸下的物品放回背包
            inventory.add_item(old_item)
            return True, f"已卸下 {old_item.name} 并放回背包"
        
        return success, message
    
    def draw_dragged_item(self):
        """绘制正在拖动的物品"""
        print(f"draw_dragged_item called: dragged_item={self.dragged_item is not None}, drag_current_pos={self.drag_current_pos}")
        
        if not self.dragged_item or not self.drag_current_pos:
            return
        
        mouse_x, mouse_y = self.drag_current_pos
        print(f"  -> 绘制拖动物品 at ({mouse_x}, {mouse_y}): {self.dragged_item.name}")
        
        # 绘制拖动物品的背景
        drag_width = 120
        drag_height = 40
        
        arcade.draw_lrbt_rectangle_filled(
            mouse_x - drag_width // 2,
            mouse_x + drag_width // 2,
            mouse_y - drag_height // 2,
            mouse_y + drag_height // 2,
            (80, 80, 80, 220)
        )
        
        arcade.draw_lrbt_rectangle_outline(
            mouse_x - drag_width // 2,
            mouse_x + drag_width // 2,
            mouse_y - drag_height // 2,
            mouse_y + drag_height // 2,
            arcade.color.WHITE,
            border_width=2
        )
        
        # 绘制物品名称
        arcade.draw_text(
            self.dragged_item.name,
            mouse_x,
            mouse_y,
            arcade.color.WHITE,
            font_size=S.font(11),
            bold=True,
            anchor_x="center",
            anchor_y="center"
        )

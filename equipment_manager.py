"""
装备管理系统模块
管理角色的装备槽位和装备操作
"""
from enum import Enum
from typing import Dict, List, Optional, Tuple
from inventory import InventoryItem, ItemType


class EquipmentSlot(Enum):
    """装备槽位枚举"""
    BODY = "body"           # 躯干装备(主槽位)
    WEAPON = "weapon"       # 武器槽位
    ACCESSORY = "accessory" # 饰品槽位


class EquipmentManager:
    """装备管理器"""
    
    def __init__(self, owner_name: str = ""):
        self.owner_name = owner_name
        
        # 当前装备的槽位映射: {EquipmentSlot: InventoryItem}
        self.equipped_items: Dict[EquipmentSlot, Optional[InventoryItem]] = {
            EquipmentSlot.BODY: None,
            EquipmentSlot.WEAPON: None,
            EquipmentSlot.ACCESSORY: None,
        }
        
        # 已解锁的槽位列表(用于扩展)
        self.unlocked_slots: List[EquipmentSlot] = [
            EquipmentSlot.BODY,
            EquipmentSlot.WEAPON,
            EquipmentSlot.ACCESSORY,
        ]
        
        # 战斗中标记（战斗中不能更换装备）
        self.in_combat = False
        
        # 更换武器的AP消耗
        self.weapon_swap_ap_cost = 2
    
    def can_equip(self, item: InventoryItem, slot: EquipmentSlot, entity=None) -> Tuple[bool, str]:
        """
        检查物品是否可以装备到指定槽位
        
        Args:
            item: 要装备的物品
            slot: 目标槽位
            entity: 实体对象（用于检查AP）
            
        Returns:
            (是否可以装备, 原因说明)
        """
        # 检查是否在战斗中
        if self.in_combat and slot == EquipmentSlot.BODY:
            return False, "战斗中不能更换装备！"
        
        # 检查槽位是否解锁
        if slot not in self.unlocked_slots:
            return False, f"槽位 {slot.value} 未解锁"
        
        # 检查物品类型是否匹配槽位
        if slot == EquipmentSlot.WEAPON and item.item_type != ItemType.WEAPON:
            return False, "武器槽位只能装备武器"
        
        if slot == EquipmentSlot.BODY and item.item_type != ItemType.ARMOR:
            return False, "身体槽位只能装备防具"
        
        if slot == EquipmentSlot.ACCESSORY and item.item_type != ItemType.ACCESSORY:
            return False, "饰品槽位只能装备饰品"
        
        # 检查AP是否足够（仅武器需要AP）
        if slot == EquipmentSlot.WEAPON and entity:
            if hasattr(entity, 'ap'):
                if entity.ap < self.weapon_swap_ap_cost:
                    return False, f"AP不足！更换武器需要{self.weapon_swap_ap_cost}点AP，当前{entity.ap}点"
        
        return True, "可以装备"
    
    def equip_item(self, item: InventoryItem, slot: EquipmentSlot, entity=None) -> Tuple[bool, str]:
        """
        装备物品到指定槽位
        
        Args:
            item: 要装备的物品
            slot: 目标槽位
            entity: 实体对象（用于扣除AP）
            
        Returns:
            (是否成功, 说明)
        """
        # 检查是否可以装备
        can_equip, reason = self.can_equip(item, slot, entity)
        if not can_equip:
            return False, reason
        
        # 触发装备前事件
        from event_system import trigger_event, GameEventType
        event_data = {
            "item": item,
            "slot": slot,
            "entity": entity
        }
        trigger_event(GameEventType.EQUIP_BEFORE, self, entity, event_data)
        
        # 如果槽位已有装备，先卸下
        old_item = self.equipped_items.get(slot)
        
        # 装备新物品
        self.equipped_items[slot] = item
        
        # 扣除AP（仅武器需要）
        if slot == EquipmentSlot.WEAPON and entity:
            if hasattr(entity, 'ap'):
                entity.ap -= self.weapon_swap_ap_cost
        
        # 触发装备后事件
        event_data["old_item"] = old_item
        trigger_event(GameEventType.EQUIP_AFTER, self, entity, event_data)
        
        if old_item:
            return True, f"已替换{slot.value}槽位的装备: {old_item.name} -> {item.name}"
        else:
            return True, f"已装备到{slot.value}槽位: {item.name}"
    
    def unequip_item(self, slot: EquipmentSlot) -> Tuple[bool, str, Optional[InventoryItem]]:
        """
        卸下指定槽位的装备
        
        Args:
            slot: 要卸下的槽位
            
        Returns:
            (是否成功, 说明, 卸下的物品)
        """
        item = self.equipped_items.get(slot)
        if item is None:
            return False, f"{slot.value}槽位没有装备", None
        
        # 触发卸下前事件
        from event_system import trigger_event, GameEventType
        event_data = {
            "item": item,
            "slot": slot
        }
        trigger_event(GameEventType.UNEQUIP_BEFORE, self, None, event_data)
        
        # 卸下装备
        self.equipped_items[slot] = None
        
        # 触发卸下后事件
        trigger_event(GameEventType.UNEQUIP_AFTER, self, None, event_data)
        
        return True, f"已卸下{slot.value}槽位的装备: {item.name}", item
    
    def get_equipped_item(self, slot: EquipmentSlot) -> Optional[InventoryItem]:
        """获取指定槽位的装备"""
        return self.equipped_items.get(slot)
    
    def get_all_equipped(self) -> Dict[str, Optional[InventoryItem]]:
        """
        获取所有已装备的物品
        
        Returns:
            {槽位名称: 物品} 字典
        """
        return {slot.value: item for slot, item in self.equipped_items.items()}
    
    def swap_equipment(self, item: InventoryItem, slot: EquipmentSlot, entity=None) -> Tuple[bool, str, Optional[InventoryItem]]:
        """
        交换装备(装备新物品并返回旧物品)
        
        Args:
            item: 要装备的新物品
            slot: 目标槽位
            entity: 实体对象（用于扣除AP）
            
        Returns:
            (是否成功, 说明, 被替换的旧物品)
        """
        can_equip, reason = self.can_equip(item, slot, entity)
        if not can_equip:
            return False, reason, None
        
        old_item = self.equipped_items.get(slot)
        self.equipped_items[slot] = item
        
        # 扣除AP（仅武器需要）
        if slot == EquipmentSlot.WEAPON and entity:
            if hasattr(entity, 'ap'):
                entity.ap -= self.weapon_swap_ap_cost
        
        if old_item:
            return True, f"已替换装备", old_item
        else:
            return True, f"已装备", None
    
    def unlock_slot(self, slot: EquipmentSlot):
        """解锁新的装备槽位"""
        if slot not in self.unlocked_slots:
            self.unlocked_slots.append(slot)
            if slot not in self.equipped_items:
                self.equipped_items[slot] = None
    
    def get_stats_summary(self) -> Dict[str, any]:
        """
        获取装备属性摘要
        
        Returns:
            包含装备属性的字典
        """
        summary = {
            "total_slots": len(self.unlocked_slots),
            "equipped_count": sum(1 for item in self.equipped_items.values() if item is not None),
            "slots": {}
        }
        
        for slot in self.unlocked_slots:
            item = self.equipped_items.get(slot)
            summary["slots"][slot.value] = {
                "unlocked": True,
                "equipped": item is not None,
                "item_name": item.name if item else None,
                "item_type": item.item_type.value if item else None,
            }
        
        return summary
    
    def __str__(self):
        equipped_count = sum(1 for item in self.equipped_items.values() if item is not None)
        return f"EquipmentManager({self.owner_name}): {equipped_count}/{len(self.unlocked_slots)} 槽位已装备"

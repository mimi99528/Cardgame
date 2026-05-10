"""
玩家牌库系统模块
管理玩家获得但未加入卡组的卡牌收藏
"""
from typing import Dict, List, Optional, TYPE_CHECKING
from copy import deepcopy
import json
import os

from card_serializer import CardSerializer
from config import Rarity

if TYPE_CHECKING:
    from models import Card


class PlayerCardLibrary:
    """
    玩家牌库系统
    存储和管理玩家获得的所有卡牌（包括已加入卡组和未加入卡组的）
    """
    
    def __init__(self, owner_name: str = "player"):
        self.owner_name = owner_name
        # 牌库：存储所有获得的卡牌（按名称分组）
        self.library: Dict[str, List['Card']] = {}
        # 卡组：当前正在使用的卡牌列表
        self.deck: List['Card'] = []
        # 最大牌库容量
        self.max_capacity = 200
    
    @property
    def total_cards(self) -> int:
        """获取牌库中卡牌总数"""
        return sum(len(cards) for cards in self.library.values())
    
    @property
    def unique_cards(self) -> int:
        """获取不同卡牌种类数"""
        return len(self.library)
    
    def add_card_to_library(self, card: 'Card') -> bool:
        """
        添加卡牌到牌库（获得新卡牌）
        
        Args:
            card: 要添加的卡牌
            
        Returns:
            是否成功添加
        """
        if self.total_cards >= self.max_capacity:
            return False
        
        if card.name not in self.library:
            self.library[card.name] = []
        
        # 添加卡牌副本到牌库
        card_copy = card.copy()
        self.library[card.name].append(card_copy)
        return True
    
    def remove_card_from_library(self, card_name: str, index: int = 0) -> Optional['Card']:
        """
        从牌库移除卡牌
        
        Args:
            card_name: 卡牌名称
            index: 卡牌索引（同名卡牌可能有多个）
            
        Returns:
            被移除的卡牌，如果不存在则返回None
        """
        if card_name in self.library and len(self.library[card_name]) > index:
            removed_card = self.library[card_name].pop(index)
            
            # 如果该名称下没有卡牌了，删除键
            if not self.library[card_name]:
                del self.library[card_name]
            
            return removed_card
        return None
    
    def add_card_to_deck(self, card_name: str, index: int = 0) -> bool:
        """
        从牌库添加卡牌到卡组（移动卡牌，不是复制）
        
        Args:
            card_name: 卡牌名称
            index: 牌库中卡牌的索引
            
        Returns:
            是否成功添加
        """
        # 调试信息
        print(f"[DEBUG] 尝试添加卡牌: {card_name}")
        print(f"[DEBUG] 当前卡组大小: {len(self.deck)}")
        print(f"[DEBUG] 牌库中的卡牌: {list(self.library.keys())}")
        
        # 检查卡组大小限制（12-28张）
        if len(self.deck) >= 28:
            print(f"[DEBUG] 添加失败：卡组已满（{len(self.deck)}/28）")
            return False
        
        # 从牌库获取卡牌
        if card_name not in self.library or len(self.library[card_name]) <= index:
            print(f"[DEBUG] 添加失败：牌库中没有该卡牌（{card_name}，当前库存: {self.get_card_count_in_library(card_name)}）")
            return False
        
        # 关键修复：在移动卡牌之前先计算卡组中的数量
        # 因为 add_card_to_deck 是从牌库 pop 到卡组，所以 deck 计数会逐渐增加
        card_count_in_deck = sum(1 for c in self.deck if c.name == card_name)
        max_count = self._get_max_card_count_by_name(card_name)
        
        print(f"[DEBUG] 准备移动前 - 卡组中已有: {card_count_in_deck}/{max_count}")
        
        if card_count_in_deck >= max_count:
            print(f"[DEBUG] 添加失败：同名卡牌已达上限")
            return False
        
        # 从牌库中移除卡牌（移动，不是复制）
        card = self.library[card_name].pop(index)
        print(f"[DEBUG] 从牌库中移除卡牌: {card_name}")
        
        # 如果该名称下没有卡牌了，删除键
        if not self.library[card_name]:
            del self.library[card_name]
        
        # 添加到卡组
        self.deck.append(card)
        print(f"[DEBUG] 成功添加卡牌: {card_name}，当前卡组大小: {len(self.deck)}")
        return True
    
    def remove_card_from_deck(self, card_index: int) -> Optional['Card']:
        """
        从卡组移除卡牌（返回牌库）
        
        Args:
            card_index: 卡组中的卡牌索引
            
        Returns:
            被移除的卡牌，如果索引无效则返回None
        """
        # 移除卡组大小限制检查，允许临时减少到12张以下
        # 只在退出编辑时验证卡组大小
        
        if 0 <= card_index < len(self.deck):
            removed_card = self.deck.pop(card_index)
            # 将卡牌返回牌库
            self.add_card_to_library(removed_card)
            return removed_card
        return None
    
    def get_card_from_library(self, card_name: str, index: int = 0) -> Optional['Card']:
        """获取牌库中的卡牌"""
        if card_name in self.library and len(self.library[card_name]) > index:
            return self.library[card_name][index]
        return None
    
    def get_cards_by_name(self, card_name: str) -> List['Card']:
        """获取指定名称的所有卡牌"""
        return self.library.get(card_name, []).copy()
    
    def get_all_library_cards(self) -> List['Card']:
        """获取牌库中所有卡牌"""
        all_cards = []
        for cards in self.library.values():
            all_cards.extend(cards)
        return all_cards
    
    def get_available_cards_for_deck(self) -> List['Card']:
        """
        获取可用于添加到卡组的卡牌（从牌库中）
        返回牌库中所有卡牌（按名称去重，只显示一个代表）
        
        Returns:
            可用于添加的卡牌列表（每种卡牌一个代表）
        """
        available_cards = []
        
        for card_name, cards in self.library.items():
            if not cards:
                continue
            
            # 检查该卡牌是否还可以添加到卡组
            if self.can_add_to_deck(card_name):
                # 只返回一个代表卡牌用于显示
                available_cards.append(cards[0])
        
        return available_cards
    
    def get_all_cards_in_library(self) -> List['Card']:
        """
        获取牌库中所有卡牌（不去重）
        用于显示牌库中的所有卡牌
        
        Returns:
            牌库中所有卡牌的列表
        """
        all_cards = []
        for cards in self.library.values():
            all_cards.extend(cards)
        return all_cards
    
    def has_card_in_library(self, card_name: str) -> bool:
        """检查牌库中是否拥有指定卡牌"""
        return card_name in self.library and len(self.library[card_name]) > 0
    
    def get_card_count_in_library(self, card_name: str) -> int:
        """获取牌库中指定卡牌的数量"""
        return len(self.library.get(card_name, []))
    
    def get_deck_info(self) -> Dict:
        """获取卡组信息"""
        # 统计卡组中各稀有度卡牌数量
        rarity_counts = {
            "COMMON": 0,
            "UNCOMMON": 0,
            "RARE": 0,
            "LEGENDARY": 0
        }
        
        for card in self.deck:
            if card.rarity.name in rarity_counts:
                rarity_counts[card.rarity.name] += 1
        
        return {
            "deck_size": len(self.deck),
            "min_deck_size": 12,
            "max_deck_size": 28,
            "rarity_counts": rarity_counts,
            "unique_cards_in_deck": len(set(c.name for c in self.deck))
        }
    
    def get_library_info(self) -> Dict:
        """获取牌库信息"""
        return {
            "total_cards": self.total_cards,
            "max_capacity": self.max_capacity,
            "unique_cards": self.unique_cards,
            "capacity_usage": self.total_cards / self.max_capacity if self.max_capacity > 0 else 0
        }
    
    def _get_max_card_count_by_name(self, card_name: str) -> int:
        """
        根据卡牌稀有度获取卡组中同名卡牌的最大数量
        
        Args:
            card_name: 卡牌名称
            
        Returns:
            最大数量限制
        """
        # 首先尝试从牌库中获取卡牌以确定稀有度
        if card_name in self.library and len(self.library[card_name]) > 0:
            card = self.library[card_name][0]
            rarity = card.rarity
        else:
            # 如果牌库中没有，从卡组中查找
            card_in_deck = next((c for c in self.deck if c.name == card_name), None)
            if card_in_deck:
                rarity = card_in_deck.rarity
            else:
                # 真的找不到才默认返回3（普通卡）
                return 3
        
        # 四种稀有度的上限：普通3/优秀2/稀有2/传说1
        max_counts = {
            Rarity.COMMON: 3,
            Rarity.UNCOMMON: 2,
            Rarity.RARE: 2,
            Rarity.LEGENDARY: 1
        }
        
        return max_counts.get(rarity, 1)
    
    def can_add_to_deck(self, card_name: str) -> bool:
        """
        检查是否可以将指定卡牌添加到卡组
        
        Args:
            card_name: 卡牌名称
            
        Returns:
            是否可以添加
        """
        # 检查卡组大小
        if len(self.deck) >= 28:
            return False
        
        # 检查同名卡牌数量
        card_count_in_deck = sum(1 for c in self.deck if c.name == card_name)
        max_count = self._get_max_card_count_by_name(card_name)
        
        return card_count_in_deck < max_count
    
    def validate_deck_for_battle(self) -> tuple:
        """
        验证卡组是否符合战斗要求（用于退出编辑时检查）
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查卡组大小
        deck_size = len(self.deck)
        if deck_size < 12:
            errors.append(f"卡组过少：当前{deck_size}张，最少需要12张")
        elif deck_size > 28:
            errors.append(f"卡组过多：当前{deck_size}张，最多允许28张")
        
        # 检查同名卡牌数量限制
        card_counts = {}
        for card in self.deck:
            name = card.name
            if name not in card_counts:
                card_counts[name] = 0
            card_counts[name] += 1
        
        for card_name, count in card_counts.items():
            max_count = self._get_max_card_count_by_name(card_name)
            if count > max_count:
                errors.append(f"{card_name} 数量超限：当前{count}张，最多允许{max_count}张")
        
        is_valid = len(errors) == 0
        return (is_valid, errors)
    
    def save_to_file(self, filepath: str):
        """
        保存牌库到文件
        
        Args:
            filepath: 文件路径
        """
        data = self.save_to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_to_dict(self) -> Dict:
        """
        保存牌库到字典
        
        Returns:
            包含牌库数据的字典
        """
        data = {
            "owner_name": self.owner_name,
            "library": {},
            "deck": []
        }
        
        # 序列化牌库
        for card_name, cards in self.library.items():
            data["library"][card_name] = [
                CardSerializer.card_to_dict(card, card_id=i)
                for i, card in enumerate(cards)
            ]
        
        # 序列化卡组
        data["deck"] = [
            CardSerializer.card_to_dict(card, card_id=i)
            for i, card in enumerate(self.deck)
        ]
        
        return data
    
    def load_from_file(self, filepath: str) -> bool:
        """
        从文件加载牌库
        
        Args:
            filepath: 文件路径
            
        Returns:
            是否成功加载
        """
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self.load_from_dict(data)
        except Exception as e:
            print(f"加载牌库失败: {e}")
            return False
    
    def load_from_dict(self, data: Dict) -> bool:
        """
        从字典加载牌库
        
        Args:
            data: 包含牌库数据的字典
            
        Returns:
            是否成功加载
        """
        try:
            self.owner_name = data.get("owner_name", "player")
            
            # 清空现有数据
            self.library.clear()
            self.deck.clear()
            
            # 加载牌库
            for card_name, cards_data in data.get("library", {}).items():
                self.library[card_name] = [
                    CardSerializer.dict_to_card(card_data)
                    for card_data in cards_data
                ]
            
            # 加载卡组
            self.deck = [
                CardSerializer.dict_to_card(card_data)
                for card_data in data.get("deck", [])
            ]
            
            return True
        except Exception as e:
            print(f"加载牌库失败: {e}")
            return False
    
    def create_starter_deck(self, starter_cards: List[str]):
        """
        创建初始卡组（用于新玩家）
        
        Args:
            starter_cards: 初始卡牌名称列表
        """
        from card_database import create_card_database
        
        cards_db = create_card_database()
        
        # 清空现有卡组
        self.deck.clear()
        
        # 添加初始卡牌到卡组
        for card_name in starter_cards:
            if card_name in cards_db:
                # 添加卡牌到牌库
                card = cards_db[card_name]
                self.add_card_to_library(card)
                
                # 添加卡牌到卡组
                if self.can_add_to_deck(card_name):
                    self.add_card_to_deck(card_name)
    
    def __str__(self):
        return f"PlayerCardLibrary({self.owner_name}, 牌库:{self.total_cards}张, 卡组:{len(self.deck)}张)"
    
    def __repr__(self):
        return self.__str__()

"""
地图节点系统模块
使用networkx图论库和面向对象编程实现地图系统
"""
import networkx as nx
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class NodeType(Enum):
    """节点类型枚举"""
    SAFE_ZONE = "安全区"        # 村庄/营地
    BATTLE_ZONE = "战斗区"      # 废墟/洞穴
    NARRATIVE_ZONE = "叙事区"   # 祭坛/古树


@dataclass
class MapNode:
    """地图节点类 - 表示地图上的一个位置点"""
    
    node_id: str                        # 节点唯一ID
    name: str                           # 节点名称
    description: str                    # 节点描述
    node_type: NodeType                 # 节点类型
    position: Tuple[float, float]       # 节点在地图上的位置 (x, y)
    tags: List[str] = field(default_factory=list)  # 节点标签列表
    
    # 节点属性
    food_cost: int = 1                  # 移动到此节点消耗的食物
    time_cost: int = 1                  # 移动到此节点消耗的时间
    is_visited: bool = False            # 是否已访问
    is_current: bool = False            # 是否是玩家当前所在节点
    is_cleared: bool = False            # 是否已被清剿（战斗节点完成后标记为安全）
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "node_id": self.node_id,
            "name": self.name,
            "description": self.description,
            "node_type": self.node_type.value,
            "position": list(self.position),
            "tags": self.tags,
            "food_cost": self.food_cost,
            "time_cost": self.time_cost,
            "is_visited": self.is_visited,
            "is_current": self.is_current,
            "is_cleared": self.is_cleared
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MapNode':
        """从字典反序列化"""
        return MapNode(
            node_id=data["node_id"],
            name=data["name"],
            description=data["description"],
            node_type=NodeType(data["node_type"]),
            position=tuple(data["position"]),
            tags=data.get("tags", []),
            food_cost=data.get("food_cost", 1),
            time_cost=data.get("time_cost", 1),
            is_visited=data.get("is_visited", False),
            is_current=data.get("is_current", False),
            is_cleared=data.get("is_cleared", False)
        )
    
    def __str__(self) -> str:
        return f"MapNode({self.name}, type={self.node_type.value})"


class MapEdge:
    """地图边类 - 表示两个节点之间的连接"""
    
    def __init__(self, source_id: str, target_id: str, 
                 movement_cost: int = 1, description: str = ""):
        """
        初始化地图边
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            movement_cost: 移动成本（食物/时间）
            description: 边的描述
        """
        self.source_id = source_id
        self.target_id = target_id
        self.movement_cost = movement_cost
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "movement_cost": self.movement_cost,
            "description": self.description
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MapEdge':
        """从字典反序列化"""
        return MapEdge(
            source_id=data["source_id"],
            target_id=data["target_id"],
            movement_cost=data.get("movement_cost", 1),
            description=data.get("description", "")
        )
    
    def __str__(self) -> str:
        return f"MapEdge({self.source_id} -> {self.target_id}, cost={self.movement_cost})"


class MapSystem:
    """地图系统 - 使用networkx管理地图节点和连接"""
    
    def __init__(self):
        """初始化地图系统"""
        self.graph = nx.Graph()  # 无向图，支持双向移动
        self.nodes: Dict[str, MapNode] = {}
        self.edges: Dict[Tuple[str, str], MapEdge] = {}
        self.current_node_id: Optional[str] = None
        
        # 叙事节点触发记录（防止重复触发）
        self.completed_narratives: set = set()  # 记录已完成的叙事节点ID
        
        # 玩家资源管理
        from map_resource_manager import PlayerResources, MapResourceManager
        self.player_resources = PlayerResources()
        self.resource_manager = MapResourceManager(self.player_resources)
    
    def add_node(self, node: MapNode):
        """添加节点到地图"""
        self.nodes[node.node_id] = node
        self.graph.add_node(node.node_id, pos=node.position)
        
        # 如果是当前节点，更新状态
        if node.is_current:
            self.set_current_node(node.node_id)
    
    def remove_node(self, node_id: str):
        """从地图移除节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.graph.remove_node(node_id)
            
            # 清理相关的边
            edges_to_remove = [
                edge_key for edge_key in self.edges.keys()
                if node_id in edge_key
            ]
            for edge_key in edges_to_remove:
                del self.edges[edge_key]
    
    def add_edge(self, edge: MapEdge):
        """添加边到地图"""
        # 确保两个节点都存在
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError(f"无法添加边：节点 {edge.source_id} 或 {edge.target_id} 不存在")
        
        edge_key = (edge.source_id, edge.target_id)
        self.edges[edge_key] = edge
        self.graph.add_edge(edge.source_id, edge.target_id, weight=edge.movement_cost)
    
    def remove_edge(self, source_id: str, target_id: str):
        """从地图移除边"""
        edge_key = (source_id, target_id)
        if edge_key in self.edges:
            del self.edges[edge_key]
            self.graph.remove_edge(source_id, target_id)
    
    def set_current_node(self, node_id: str):
        """设置玩家当前所在节点"""
        if node_id not in self.nodes:
            raise ValueError(f"节点 {node_id} 不存在")
        
        # 清除之前的当前节点标记
        if self.current_node_id and self.current_node_id in self.nodes:
            self.nodes[self.current_node_id].is_current = False
        
        # 设置新的当前节点
        self.current_node_id = node_id
        self.nodes[node_id].is_current = True
        self.nodes[node_id].is_visited = True
    
    def get_node(self, node_id: str) -> Optional[MapNode]:
        """根据ID获取节点"""
        return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[MapNode]:
        """获取所有节点"""
        return list(self.nodes.values())
    
    def get_connected_nodes(self, node_id: str) -> List[MapNode]:
        """获取与指定节点相连的所有节点"""
        if node_id not in self.graph:
            return []
        
        connected_ids = list(self.graph.neighbors(node_id))
        return [self.nodes[nid] for nid in connected_ids if nid in self.nodes]
    
    def get_edge(self, source_id: str, target_id: str) -> Optional[MapEdge]:
        """获取两个节点之间的边"""
        # 尝试正向
        edge_key = (source_id, target_id)
        if edge_key in self.edges:
            return self.edges[edge_key]
        
        # 尝试反向（无向图）
        edge_key = (target_id, source_id)
        if edge_key in self.edges:
            return self.edges[edge_key]
        
        return None
    
    def can_move_to(self, target_node_id: str) -> bool:
        """检查是否可以移动到目标节点"""
        if not self.current_node_id:
            return False
        
        if target_node_id not in self.graph:
            return False
        
        # 检查是否有路径
        return nx.has_path(self.graph, self.current_node_id, target_node_id)
    
    def move_to_node(self, target_node_id: str) -> Tuple[bool, str]:
        """
        移动到目标节点
        
        Returns:
            (成功标志, 消息)
        """
        if not self.can_move_to(target_node_id):
            return False, f"无法移动到节点 {target_node_id}"
        
        target_node = self.nodes[target_node_id]
        
        # 检查资源是否足够（食物、时间等）
        success, message = self.resource_manager.try_move_to_node(target_node)
        
        if not success:
            return False, message
        
        old_node_id = self.current_node_id
        self.set_current_node(target_node_id)
        
        # 触发节点移动事件（用于执念系统等）
        from event_system import trigger_event, GameEventType
        trigger_event(
            GameEventType.NODE_TRAVEL,
            source=self.nodes.get(old_node_id),
            target=target_node,
            data={
                "old_node_id": old_node_id,
                "new_node_id": target_node_id,
                "node_type": target_node.node_type.value
            }
        )
        
        return True, f"从 {self.nodes[old_node_id].name} 移动到 {target_node.name} | {message}"
    
    def get_shortest_path(self, target_node_id: str) -> Optional[List[str]]:
        """获取到目标节点的最短路径"""
        if not self.current_node_id:
            return None
        
        try:
            path = nx.shortest_path(
                self.graph, 
                self.current_node_id, 
                target_node_id,
                weight='weight'
            )
            return path
        except nx.NetworkXNoPath:
            return None
    
    def clear_node(self, node_id: str) -> bool:
        """
        标记节点为已清剿（战斗完成后调用）
        
        Args:
            node_id: 节点ID
            
        Returns:
            是否成功标记
        """
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        node.is_cleared = True
        # 清剿后，战斗节点变为安全区
        if node.node_type == NodeType.BATTLE_ZONE:
            node.food_cost = max(0, node.food_cost - 1)  # 减少食物消耗
            print(f"[地图] 节点 {node.name} 已被清剿，现在更安全了")
        
        return True
    
    def mark_narrative_completed(self, node_id: str) -> bool:
        """
        标记叙事节点为已完成（防止重复触发）
        
        Args:
            node_id: 叙事节点ID（如 altar_site_001）
            
        Returns:
            是否成功标记
        """
        self.completed_narratives.add(node_id)
        print(f"[地图] 叙事节点 {node_id} 已标记为完成，不可重复触发")
        return True
    
    def is_narrative_completed(self, node_id: str) -> bool:
        """
        检查叙事节点是否已完成
        
        Args:
            node_id: 叙事节点ID
            
        Returns:
            是否已完成
        """
        return node_id in self.completed_narratives
    
    def save_to_file(self, filepath: str):
        """保存地图到JSON文件（包括玩家资源状态和叙事节点完成状态）"""
        import json
        
        data = {
            "current_node_id": self.current_node_id,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()],
            # 保存玩家资源状态
            "player_resources": {
                "food_units": self.player_resources.food_units,
                "max_food_units": self.player_resources.max_food_units,
                "current_day": self.player_resources.current_day,
                "current_time": self.player_resources.current_time,
                "gold": self.player_resources.gold,
                "luck_points": self.player_resources.luck_points
            },
            # 保存叙事节点完成状态
            "completed_narratives": list(self.completed_narratives)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[地图] 已保存地图、资源状态和叙事进度到 {filepath}")
    
    def load_from_file(self, filepath: str):
        """从 JSON文件加载地图（包括玩家资源状态和叙事节点完成状态）"""
        import json
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 清空现有数据
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()
            
        # 加载节点
        for node_data in data.get("nodes", []):
            node = MapNode.from_dict(node_data)
            self.add_node(node)
            
        # 加载边
        for edge_data in data.get("edges", []):
            edge = MapEdge.from_dict(edge_data)
            self.add_edge(edge)
            
        # 设置当前节点
        current_node_id = data.get("current_node_id")
        if current_node_id and current_node_id in self.nodes:
            self.set_current_node(current_node_id)
            
        # 加载玩家资源状态
        resources_data = data.get("player_resources")
        if resources_data:
            self.player_resources.food_units = resources_data.get("food_units", 10)
            self.player_resources.max_food_units = resources_data.get("max_food_units", 20)
            self.player_resources.current_day = resources_data.get("current_day", 1)
            self.player_resources.current_time = resources_data.get("current_time", 0)
            self.player_resources.gold = resources_data.get("gold", 50)
            self.player_resources.luck_points = resources_data.get("luck_points", 3)
            print(f"[地图] 已加载玩家资源状态")
        else:
            print(f"[地图] 未找到玩家资源数据，使用默认值")
        
        # 加载叙事节点完成状态
        completed_narratives_data = data.get("completed_narratives", [])
        if completed_narratives_data:
            self.completed_narratives = set(completed_narratives_data)
            print(f"[地图] 已加载 {len(self.completed_narratives)} 个已完成的叙事节点: {self.completed_narratives}")
        else:
            print(f"[地图] 未找到叙事节点完成状态数据")
    
    def create_example_map(self):
        """创建示例地图（3-5个节点）"""
        # 清空现有地图
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()
        
        # 创建节点
        nodes = [
            MapNode(
                node_id="village_001",
                name="新手村庄",
                description="一个宁静的小村庄，是冒险者的起点。",
                node_type=NodeType.SAFE_ZONE,
                position=(200, 300),
                tags=["村庄", "安全", "起始点"],
                food_cost=0,
                time_cost=0,
                is_current=True
            ),
            MapNode(
                node_id="ruins_001",
                name="古老废墟",
                description="一片破败的古代建筑遗迹，据说隐藏着宝藏。",
                node_type=NodeType.BATTLE_ZONE,
                position=(500, 300),
                tags=["废墟", "战斗", "宝藏"],
                food_cost=2,
                time_cost=1
            ),
            MapNode(
                node_id="altar_001",
                name="神秘祭坛",
                description="一座古老的祭坛，散发着神秘的能量。",
                node_type=NodeType.NARRATIVE_ZONE,
                position=(350, 500),
                tags=["祭坛", "叙事", "神秘"],
                food_cost=1,
                time_cost=1
            ),
            MapNode(
                node_id="cave_001",
                name="黑暗洞穴",
                description="一个深邃的洞穴，里面可能有危险的生物。",
                node_type=NodeType.BATTLE_ZONE,
                position=(650, 500),
                tags=["洞穴", "战斗", "危险"],
                food_cost=3,
                time_cost=2
            ),
            MapNode(
                node_id="camp_001",
                name="旅行者营地",
                description="一个临时的营地，旅者可以在此休息。",
                node_type=NodeType.SAFE_ZONE,
                position=(500, 150),
                tags=["营地", "安全", "休息"],
                food_cost=1,
                time_cost=1
            )
        ]
        
        # 添加节点
        for node in nodes:
            self.add_node(node)
        
        # 创建边（连接线）
        edges = [
            MapEdge("village_001", "ruins_001", movement_cost=2, description="通往废墟的道路"),
            MapEdge("village_001", "altar_001", movement_cost=1, description="小径通向祭坛"),
            MapEdge("ruins_001", "cave_001", movement_cost=3, description="崎岖的山路"),
            MapEdge("ruins_001", "camp_001", movement_cost=1, description="平坦的道路"),
            MapEdge("altar_001", "cave_001", movement_cost=2, description="穿过森林的小路"),
            MapEdge("camp_001", "cave_001", movement_cost=2, description="绕行山路")
        ]
        
        # 添加边
        for edge in edges:
            self.add_edge(edge)
        
        print(f"[地图] 创建了示例地图：{len(nodes)}个节点，{len(edges)}条边")


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("地图系统测试")
    print("=" * 60)
    
    # 创建地图系统
    map_system = MapSystem()
    map_system.create_example_map()
    
    # 显示所有节点
    print("\n所有节点:")
    for node in map_system.get_all_nodes():
        current_marker = " ← 当前位置" if node.is_current else ""
        print(f"  - {node}{current_marker}")
    
    # 显示当前节点的连接
    current_node = map_system.nodes[map_system.current_node_id]
    print(f"\n当前节点: {current_node.name}")
    print("可连接的节点:")
    for connected in map_system.get_connected_nodes(map_system.current_node_id):
        edge = map_system.get_edge(map_system.current_node_id, connected.node_id)
        print(f"  - {connected.name} (移动成本: {edge.movement_cost})")
    
    # 测试移动
    print("\n测试移动到古老废墟...")
    success, message = map_system.move_to_node("ruins_001")
    print(f"  结果: {message}")
    
    # 再次显示连接
    current_node = map_system.nodes[map_system.current_node_id]
    print(f"\n当前节点: {current_node.name}")
    print("可连接的节点:")
    for connected in map_system.get_connected_nodes(map_system.current_node_id):
        edge = map_system.get_edge(map_system.current_node_id, connected.node_id)
        print(f"  - {connected.name} (移动成本: {edge.movement_cost})")
    
    # 保存地图
    map_system.save_to_file("test_map.json")
    print("\n✓ 地图已保存到 test_map.json")
    
    # 加载地图
    map_system2 = MapSystem()
    map_system2.load_from_file("test_map.json")
    print("✓ 地图已从文件加载")
    print(f"  当前节点: {map_system2.nodes[map_system2.current_node_id].name}")
    
    print("\n" + "=" * 60)

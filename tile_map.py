"""
瓦片地图系统模块
负责生成和管理瓦片地图
"""
import random
import heapq
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class Tile:
    """瓦片类"""
    x: int  # 网格坐标x
    y: int  # 网格坐标y
    tile_type: str  # 瓦片类型: 'grass', 'water', 'obstacle'等
    color: Tuple[int, int, int]  # RGB颜色
    terrain_type: str = 'normal'  # 地形类型: 'normal'(普通), 'difficult'(困难), 'obstacle'(障碍)
    is_walkable: bool = True  # 是否可通行
    md_cost: int = 1  # 移动到此格消耗的MD（默认1，困难地形为2）


class TileMap:
    """瓦片地图类"""
    
    def __init__(self, width: int = 20, height: int = 15):
        self.width = width
        self.height = height
        self.tiles: List[List[Tile]] = []
        self.tile_size = 40  # 每个瓦片的像素大小
        
        # 定义颜色
        self.colors = {
            'grass_light': (144, 238, 144),   # 浅绿色
            'grass_dark': (34, 139, 34),      # 深绿色
            'water': (30, 144, 255),          # 蓝色（己方）
            'enemy': (255, 69, 0),            # 红色（敌方）
            'range': (0, 100, 0),             # 深绿色（射程范围）
            'highlight': (255, 255, 0),       # 黄色（高亮）
            'difficult': (210, 180, 140),     # 褐色（困难地形）
            'obstacle': (105, 105, 105),      # 灰色（障碍物）
        }
        
        # 初始化地图
        self._generate_map()
        self._save_original_colors()  # 保存原始颜色
    
    def _generate_map(self):
        """生成随机地图"""
        self.tiles = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # 使用固定的模式而不是随机，确保每次相同
                # 使用棋盘格模式交替两种绿色
                if (x + y) % 2 == 0:
                    color = self.colors['grass_light']
                    terrain_type = 'normal'
                    is_walkable = True
                    md_cost = 1
                else:
                    color = self.colors['grass_dark']
                    terrain_type = 'normal'
                    is_walkable = True
                    md_cost = 1
                
                # 添加一些障碍物和困难地形作为示例
                # 障碍物示例
                if (x == 5 and y == 7) or (x == 10 and y == 3) or (x == 15 and y == 10):
                    color = self.colors['obstacle']
                    terrain_type = 'obstacle'
                    is_walkable = False
                    md_cost = 0
                # 困难地形示例
                elif (x == 8 and y == 5) or (x == 12 and y == 8) or (x == 6 and y == 12):
                    color = self.colors['difficult']
                    terrain_type = 'difficult'
                    is_walkable = True
                    md_cost = 2
                
                tile = Tile(
                    x=x,
                    y=y,
                    tile_type='grass',
                    terrain_type=terrain_type,
                    color=color,
                    is_walkable=is_walkable,
                    md_cost=md_cost
                )
                row.append(tile)
            self.tiles.append(row)
    
    def _save_original_colors(self):
        """保存原始颜色以便重置"""
        self.original_colors = []
        for row in self.tiles:
            color_row = []
            for tile in row:
                color_row.append(tile.color)
            self.original_colors.append(color_row)
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """获取指定位置的瓦片"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None
    
    def get_tile_at_pixel(self, pixel_x: float, pixel_y: float) -> Optional[Tile]:
        """根据像素坐标获取瓦片"""
        grid_x = int(pixel_x / self.tile_size)
        grid_y = int(pixel_y / self.tile_size)
        return self.get_tile(grid_x, grid_y)
    
    def get_valid_moves(self, start_x: int, start_y: int, max_distance: int) -> List[Tuple[int, int]]:
        """获取从起点出发在最大距离内的所有可移动位置"""
        valid_moves = []
        for y in range(self.height):
            for x in range(self.width):
                distance = abs(x - start_x) + abs(y - start_y)  # 曼哈顿距离
                if distance <= max_distance and distance > 0:
                    tile = self.get_tile(x, y)
                    if tile and tile.is_walkable:
                        valid_moves.append((x, y))
        return valid_moves
    
    def get_tile_pixel_pos(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """获取瓦片的像素中心位置"""
        pixel_x = grid_x * self.tile_size + self.tile_size / 2
        pixel_y = grid_y * self.tile_size + self.tile_size / 2
        return pixel_x, pixel_y
    
    def highlight_range(self, center_x: int, center_y: int, max_distance: int):
        """高亮显示范围内的瓦片"""
        # 高亮显示范围内的瓦片
        for y in range(self.height):
            for x in range(self.width):
                distance = abs(x - center_x) + abs(y - center_y)
                if distance <= max_distance:
                    tile = self.get_tile(x, y)
                    if tile:
                        tile.color = self.colors['range']
                else:
                    # 恢复原始颜色
                    tile = self.get_tile(x, y)
                    if tile and 0 <= y < len(self.original_colors) and 0 <= x < len(self.original_colors[y]):
                        tile.color = self.original_colors[y][x]
    
    def reset_highlights(self):
        """重置所有高亮"""
        for y in range(self.height):
            for x in range(self.width):
                tile = self.get_tile(x, y)
                if tile and 0 <= y < len(self.original_colors) and 0 <= x < len(self.original_colors[y]):
                    tile.color = self.original_colors[y][x]
    
    def find_path_astar(self, start: Tuple[int, int], end: Tuple[int, int], 
                       entities_positions: List[Tuple[int, int]] = None,
                       is_ally: bool = False) -> Optional[List[Tuple[int, int]]]:
        """
        使用A*算法寻找路径
        
        Args:
            start: 起始位置 (x, y)
            end: 目标位置 (x, y)
            entities_positions: 其他实体的位置列表（不能通过）
            is_ally: 如果目标是队友，允许通过但消耗双倍MD
        
        Returns:
            路径列表 [(x1,y1), (x2,y2), ...] 或 None（如果无法到达）
        """
        if entities_positions is None:
            entities_positions = []
        
        # 检查起点和终点是否有效
        start_tile = self.get_tile(start[0], start[1])
        end_tile = self.get_tile(end[0], end[1])
        
        if not start_tile or not end_tile:
            return None
        
        if not start_tile.is_walkable or not end_tile.is_walkable:
            return None
        
        # A*算法实现
        open_set = []
        counter = 0  # 用于处理优先级相同的情况
        heapq.heappush(open_set, (0, counter, start))
        
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0}
        f_score: Dict[Tuple[int, int], float] = {start: self._heuristic(start, end)}
        
        closed_set = set()
        
        while open_set:
            _, _, current = heapq.heappop(open_set)
            
            # 到达终点
            if current == end:
                return self._reconstruct_path(came_from, current)
            
            if current in closed_set:
                continue
            
            closed_set.add(current)
            
            # 检查四个方向
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # 检查边界
                neighbor_tile = self.get_tile(neighbor[0], neighbor[1])
                if not neighbor_tile:
                    continue
                
                # 检查是否可通行
                if not neighbor_tile.is_walkable:
                    continue
                
                # 检查是否有其他实体（障碍物）
                if neighbor in entities_positions:
                    # 如果是队友且目标是队友位置，允许最后一步
                    if is_ally and neighbor == end:
                        pass  # 允许移动到队友位置
                    else:
                        continue  # 不能通过其他实体
                
                # 计算移动成本
                move_cost = neighbor_tile.md_cost
                
                # 如果目标是队友位置，最后一步消耗双倍
                if is_ally and neighbor == end:
                    move_cost *= 2
                
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, end)
                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
        
        # 没有找到路径
        return None
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """启发式函数：曼哈顿距离"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _reconstruct_path(self, came_from: Dict[Tuple[int, int], Tuple[int, int]], 
                         current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """重建路径"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
    
    def calculate_path_md_cost(self, path: List[Tuple[int, int]], 
                              entities_positions: List[Tuple[int, int]] = None,
                              is_ally: bool = False) -> int:
        """
        计算路径的总MD消耗
        
        Args:
            path: 路径列表
            entities_positions: 其他实体的位置列表
            is_ally: 是否是移动到队友位置
        
        Returns:
            总MD消耗
        """
        if not path or len(path) < 2:
            return 0
        
        total_cost = 0
        for i in range(1, len(path)):
            tile = self.get_tile(path[i][0], path[i][1])
            if tile:
                cost = tile.md_cost
                # 如果目标是队友，最后一步双倍消耗
                if is_ally and i == len(path) - 1:
                    cost *= 2
                total_cost += cost
        
        return total_cost
    
    def get_valid_moves_with_md(self, start: Tuple[int, int], max_md: int,
                               entities_positions: List[Tuple[int, int]] = None) -> List[Tuple[int, int]]:
        """
        获取在MD限制内可以到达的所有位置
        
        Args:
            start: 起始位置
            max_md: 最大MD值
            entities_positions: 其他实体的位置列表
        
        Returns:
            可以到达的位置列表
        """
        if entities_positions is None:
            entities_positions = []
        
        valid_moves = []
        
        # 遍历所有可能的目标位置
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) == start:
                    continue
                
                target_tile = self.get_tile(x, y)
                if not target_tile or not target_tile.is_walkable:
                    continue
                
                # 检查是否有实体
                has_entity = (x, y) in entities_positions
                
                # 如果有实体，只允许是队友（这里简化处理，实际应该判断阵营）
                if has_entity:
                    # 暂时不允许移动到有实体的位置（需要更复杂的阵营判断）
                    continue
                
                # 尝试找路径
                path = self.find_path_astar(start, (x, y), entities_positions)
                if path:
                    # 计算MD消耗
                    md_cost = self.calculate_path_md_cost(path, entities_positions)
                    if md_cost <= max_md:
                        valid_moves.append((x, y))
        
        return valid_moves

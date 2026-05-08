"""
瓦片地图系统模块
负责生成和管理瓦片地图（Arcade 引擎版本）
支持拖动和缩放功能
"""
import random
import heapq
import arcade
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
    md_cost: int = 5  # 移动到此格消耗的MD（默认5，困难地形为10）


class TileMap:
    """瓦片地图类（Arcade 增强版）"""
    
    def __init__(self, width: int = 20, height: int = 15):
        self.width = width
        self.height = height
        self.tiles: List[List[Tile]] = []
        self.tile_size = 40  # 每个瓦片的像素大小
        
        # 相机和视图控制
        self.camera: Optional[arcade.Camera] = None
        self.gui_camera: Optional[arcade.Camera] = None
        self.view_scale = 1.0  # 缩放比例
        self.min_scale = 0.5   # 最小缩放
        self.max_scale = 2.0   # 最大缩放
        self.scroll_speed = 20  # 拖动速度
        
        # 拖动相关
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.camera_center_x = 0
        self.camera_center_y = 0
        
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
            'path': (255, 215, 0),            # 金色（路径）
            'move_range': (100, 149, 237),    # 矢车菊蓝（移动范围）
        }
        
        # 初始化地图
        self._generate_map()
        self._save_original_colors()  # 保存原始颜色
    
    def setup_cameras(self, window_width: int, window_height: int):
        """设置相机系统"""
        # 使用 Camera2D 类（Arcade 的正确 API）
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()
        
        # 初始化相机位置到地图中心
        map_pixel_width = self.width * self.tile_size
        map_pixel_height = self.height * self.tile_size
        self.camera_center_x = map_pixel_width / 2
        self.camera_center_y = map_pixel_height / 2
        
        # 设置相机初始位置和缩放
        self.camera.position = (self.camera_center_x, self.camera_center_y)
        self.camera.zoom = self.view_scale
        
        # GUI相机使用屏幕坐标系
        # 关键：position设置为窗口中心，这样屏幕左下角(0,0)对应世界坐标(0,0)
        # Camera2D的position是相机看向的中心点
        self.gui_camera.position = (window_width /2, window_height /2)
        self.gui_camera.zoom = 1.0
        
        # 保存窗口尺寸供GUI相机使用
        self.gui_window_width = window_width
        self.gui_window_height = window_height
        
        # 调试输出
        print(f"[DEBUG] Cameras setup: window={window_width}x{window_height}")
        print(f"[DEBUG] Map camera position: {self.camera.position}, zoom: {self.camera.zoom}")
        print(f"[DEBUG] GUI camera position: {self.gui_camera.position}, zoom: {self.gui_camera.zoom}")
    
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
                    md_cost = 5
                else:
                    color = self.colors['grass_dark']
                    terrain_type = 'normal'
                    is_walkable = True
                    md_cost = 5
                
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
                    md_cost = 10
                
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
    
    def _update_camera(self):
        """更新相机位置和缩放"""
        if self.camera:
            # Camera2D 直接使用位置和缩放属性
            self.camera.position = (self.camera_center_x, self.camera_center_y)
            self.camera.zoom = self.view_scale
    
    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, 
                     window_width: int, window_height: int):
        """
        处理鼠标拖动事件
        
        Args:
            x, y: 当前鼠标位置
            dx, dy: 鼠标移动增量
            window_width, window_height: 窗口尺寸
        """
        if not self.camera:
            return
        
        # 根据拖动距离移动相机
        # 注意：dx, dy 是屏幕坐标的增量，需要转换为世界坐标
        self.camera_center_x -= dx / self.view_scale
        self.camera_center_y -= dy / self.view_scale
        
        # 限制相机范围（不让地图完全移出视野）
        map_pixel_width = self.width * self.tile_size
        map_pixel_height = self.height * self.tile_size
        
        # 允许一定的边界外移（20%的地图尺寸）
        margin_x = map_pixel_width * 0.2
        margin_y = map_pixel_height * 0.2
        
        self.camera_center_x = max(-margin_x, min(map_pixel_width + margin_x, self.camera_center_x))
        self.camera_center_y = max(-margin_y, min(map_pixel_height + margin_y, self.camera_center_y))
        
        self._update_camera()
    
    def on_mouse_scroll(self, scroll_x: int, scroll_y: int):
        """
        处理鼠标滚轮事件（缩放）
        
        Args:
            scroll_x: 水平滚动量（通常不使用）
            scroll_y: 垂直滚动量（正数向上滚动=放大，负数向下滚动=缩小）
        """
        if scroll_y > 0:
            # 向上滚动 - 放大
            self.view_scale = min(self.max_scale, self.view_scale * 1.1)
        elif scroll_y < 0:
            # 向下滚动 - 缩小
            self.view_scale = max(self.min_scale, self.view_scale / 1.1)
        
        self._update_camera()
    
    def screen_to_world(self, screen_x: float, screen_y: float, 
                       window_width: float, window_height: float) -> Tuple[float, float]:
        """
        将屏幕坐标转换为世界坐标
        
        Args:
            screen_x, screen_y: 屏幕坐标
            window_width, window_height: 窗口尺寸
        
        Returns:
            世界坐标 (world_x, world_y)
        """
        if not self.camera:
            return screen_x, screen_y
        
        # Camera2D 提供了方便的转换方法
        # 使用 camera.viewport_to_world 方法
        try:
            # Arcade Camera2D 的转换方法
            world_pos = self.camera.viewport_to_world((screen_x, screen_y))
            return world_pos.x, world_pos.y
        except AttributeError:
            # 如果方法不存在，手动计算
            cam_x, cam_y = self.camera.position
            world_x = cam_x + (screen_x - window_width / 2) / self.view_scale
            world_y = cam_y + (screen_y - window_height / 2) / self.view_scale
            return world_x, world_y
    
    def world_to_grid(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """
        将世界坐标转换为网格坐标
        
        Args:
            world_x, world_y: 世界坐标
        
        Returns:
            网格坐标 (grid_x, grid_y)
        """
        grid_x = int(world_x / self.tile_size)
        grid_y = int(world_y / self.tile_size)
        return grid_x, grid_y
    
    def screen_to_grid(self, screen_x: float, screen_y: float,
                      window_width: float, window_height: float) -> Tuple[int, int]:
        """
        将屏幕坐标直接转换为网格坐标
        
        Args:
            screen_x, screen_y: 屏幕坐标
            window_width, window_height: 窗口尺寸
        
        Returns:
            网格坐标 (grid_x, grid_y)
        """
        world_x, world_y = self.screen_to_world(screen_x, screen_y, window_width, window_height)
        return self.world_to_grid(world_x, world_y)
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """获取指定位置的瓦片"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None
    
    def get_tile_at_pixel(self, pixel_x: float, pixel_y: float) -> Optional[Tile]:
        """
        根据像素坐标获取瓦片（世界坐标）
        
        Args:
            pixel_x, pixel_y: 世界坐标的像素位置
        
        Returns:
            Tile 对象或 None
        """
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
        """高亮显示范围内的瓦片（圆形范围）"""
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
    
    def highlight_attack_range(self, center_x: int, center_y: int, attack_range_config: dict):
        """
        根据攻击范围配置高亮显示瓦片
        
        Args:
            center_x: 中心点x坐标
            center_y: 中心点y坐标
            attack_range_config: 攻击范围配置字典，如 {"type": "circle", "radius": 2}
        """
        range_type = attack_range_config.get("type", "circle")
        
        # 先重置所有高亮
        self.reset_highlights()
        
        if range_type == "circle":
            radius = attack_range_config.get("radius", 1)
            self._highlight_circle_range(center_x, center_y, radius)
        elif range_type == "line":
            direction = attack_range_config.get("direction", "forward")  # forward, backward, left, right
            length = attack_range_config.get("length", 3)
            self._highlight_line_range(center_x, center_y, direction, length)
        elif range_type == "chain":
            max_targets = attack_range_config.get("max_targets", 3)
            max_distance = attack_range_config.get("max_distance", 4)
            self._highlight_chain_range(center_x, center_y, max_targets, max_distance)
        elif range_type == "cone":
            direction = attack_range_config.get("direction", "forward")
            angle = attack_range_config.get("angle", 90)  # 角度
            length = attack_range_config.get("length", 3)
            self._highlight_cone_range(center_x, center_y, direction, angle, length)
        else:
            # 默认使用圆形范围
            radius = attack_range_config.get("radius", 1)
            self._highlight_circle_range(center_x, center_y, radius)
    
    def _highlight_circle_range(self, center_x: int, center_y: int, radius: int):
        """高亮圆形范围"""
        for y in range(self.height):
            for x in range(self.width):
                # 使用曼哈顿距离
                distance = abs(x - center_x) + abs(y - center_y)
                if distance <= radius:
                    tile = self.get_tile(x, y)
                    if tile:
                        tile.color = self.colors['range']
    
    def _highlight_line_range(self, center_x: int, center_y: int, direction: str, length: int):
        """高亮直线范围"""
        positions = []
        
        if direction == "forward":  # 向上
            for i in range(1, length + 1):
                positions.append((center_x, center_y + i))
        elif direction == "backward":  # 向下
            for i in range(1, length + 1):
                positions.append((center_x, center_y - i))
        elif direction == "left":  # 向左
            for i in range(1, length + 1):
                positions.append((center_x - i, center_y))
        elif direction == "right":  # 向右
            for i in range(1, length + 1):
                positions.append((center_x + i, center_y))
        
        # 高亮这些位置
        for x, y in positions:
            if 0 <= x < self.width and 0 <= y < self.height:
                tile = self.get_tile(x, y)
                if tile:
                    tile.color = self.colors['range']
    
    def _highlight_chain_range(self, center_x: int, center_y: int, max_targets: int, max_distance: int):
        """高亮链式攻击范围（简单实现：高亮周围一定距离内的所有位置）"""
        for y in range(self.height):
            for x in range(self.width):
                distance = abs(x - center_x) + abs(y - center_y)
                if distance <= max_distance and distance > 0:  # 不包括自身
                    tile = self.get_tile(x, y)
                    if tile:
                        tile.color = self.colors['range']
    
    def _highlight_cone_range(self, center_x: int, center_y: int, direction: str, angle: int, length: int):
        """高亮锥形范围（简化实现）"""
        # 这里简化处理，实际锥形需要更复杂的几何计算
        # 暂时用矩形区域代替
        half_width = max(1, length // 2)
        
        if direction == "forward":  # 向上
            for dy in range(1, length + 1):
                for dx in range(-half_width, half_width + 1):
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        tile = self.get_tile(x, y)
                        if tile:
                            tile.color = self.colors['range']
        elif direction == "backward":  # 向下
            for dy in range(1, length + 1):
                for dx in range(-half_width, half_width + 1):
                    x, y = center_x + dx, center_y - dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        tile = self.get_tile(x, y)
                        if tile:
                            tile.color = self.colors['range']
        elif direction == "left":  # 向左
            for dx in range(1, length + 1):
                for dy in range(-half_width, half_width + 1):
                    x, y = center_x - dx, center_y + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        tile = self.get_tile(x, y)
                        if tile:
                            tile.color = self.colors['range']
        elif direction == "right":  # 向右
            for dx in range(1, length + 1):
                for dy in range(-half_width, half_width + 1):
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        tile = self.get_tile(x, y)
                        if tile:
                            tile.color = self.colors['range']
    
    def highlight_move_range(self, start_x: int, start_y: int, valid_moves: List[Tuple[int, int]]):
        """高亮显示移动范围"""
        # 先重置所有高亮
        self.reset_highlights()
        
        # 高亮可移动的位置
        for x, y in valid_moves:
            tile = self.get_tile(x, y)
            if tile:
                tile.color = self.colors['move_range']
    
    def highlight_path(self, path: List[Tuple[int, int]]):
        """高亮显示路径"""
        # 先重置所有高亮
        self.reset_highlights()
        
        # 高亮路径上的瓦片
        for x, y in path:
            tile = self.get_tile(x, y)
            if tile:
                tile.color = self.colors['path']
    
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
                    # if is_ally and neighbor == end:
                    #     pass  # 允许移动到队友位置
                    # else:
                    #     continue  # 不能通过其他实体
                    continue
                
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

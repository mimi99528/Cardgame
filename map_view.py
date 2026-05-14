"""
地图视图模块
提供地图的可视化显示和交互功能
"""
import arcade
from typing import Optional, Tuple
from map_system import MapSystem, MapNode, NodeType
from ui_scale import S


class MapView(arcade.View):
    """地图视图 - 显示地图节点和连接，支持hover和点击交互"""
    
    def __init__(self, map_system: MapSystem, window=None, player_entity=None):
        super().__init__(window=window)
        self.map_system = map_system
        self.player_entity = player_entity  # 玩家实体（用于战斗触发）
        
        # 窗口尺寸
        self.window_width = self.window.width if self.window else 1920
        self.window_height = self.window.height if self.window else 1080
        
        # 视觉配置
        self.node_radius = S.scale(20)  # 节点半径
        self.hover_radius = S.scale(25)  # hover时的半径
        self.line_width = S.scale(2)  # 连接线宽度
        
        # 颜色配置
        self.bg_color = arcade.color.BLACK  # 黑色背景
        self.node_color = arcade.color.WHITE  # 白色节点
        self.current_node_color = arcade.color.GOLD  # 当前节点金色
        self.edge_color = arcade.color.WHITE  # 白色边
        self.text_color = arcade.color.WHITE  # 白色文字
        
        # Hover状态
        self.hovered_node: Optional[MapNode] = None
        self.hovered_edge: Optional[Tuple[str, str]] = None  # (source_id, target_id)
        
        # Tooltip位置
        self.tooltip_x = 0
        self.tooltip_y = 0
        
        # UI显示状态
        self.show_equipment = False  # 是否显示装备栏
        self.show_inventory = False  # 是否显示背包栏
        
        # 战斗事件触发器
        from battle_event_trigger import BattleEventTrigger
        self.battle_trigger = BattleEventTrigger(
            map_system,
            battle_callback=self._on_battle_start
        )
    
    def _on_battle_start(self, player_team, enemy_team, node):
        """
        战斗开始回调
        
        Args:
            player_team: 玩家队伍
            enemy_team: 敌人队伍
            node: 战斗节点
        """
        print(f"\n{'='*60}")
        print(f"战斗开始！位置: {node.name}")
        print(f"敌人: {[e.name for e in enemy_team]}")
        print(f"{'='*60}\n")
        
        # 创建战斗系统并切换到战斗视图
        from battle_system import BattleSystem
        from scene_manager import BattleSceneView
        
        # 创建新的战斗系统
        battle = BattleSystem(
            player_team=player_team,
            enemy_team=enemy_team
        )
        
        # 开始战斗
        battle.start_battle()
        
        # 定义战斗结束后的回调函数
        def on_battle_end(battle_instance):
            """战斗结束后的回调"""
            print(f"\n[地图] 战斗结束，返回到大地图")
            
            # 如果战斗胜利，标记节点为已清剿
            if battle_instance.winner and battle_instance.winner == battle_instance.player_team:
                # 调用战斗事件触发器的完成处理
                if hasattr(self, 'battle_trigger'):
                    self.battle_trigger.on_battle_complete(won=True)
            
            # 注意：不需要手动切换场景，BattleSceneView会自动处理
        
        # 切换到战斗场景，传入回调函数
        battle_scene = BattleSceneView(battle, window=self.window, on_battle_end_callback=on_battle_end)
        self.window.show_view(battle_scene)
        
        print("[提示] 已切换到战斗场景")
    
    def on_resize(self, width: int, height: int):
        """窗口尺寸变化"""
        self.window_width = width
        self.window_height = height
    
    def on_draw(self):
        """绘制地图"""
        self.clear(self.bg_color)
        
        # 绘制所有边（虚线）
        self._draw_edges()
        
        # 绘制所有节点
        self._draw_nodes()
        
        # 绘制hover提示
        self._draw_tooltip()
        
        # 绘制UI提示
        self._draw_ui_hints()
        
        # 绘制资源状态栏（左上角）
        self._draw_resource_status()
    
    def _draw_edges(self):
        """绘制所有边（白色虚线）"""
        for edge in self.map_system.edges.values():
            source_node = self.map_system.nodes.get(edge.source_id)
            target_node = self.map_system.nodes.get(edge.target_id)
            
            if not source_node or not target_node:
                continue
            
            # 转换坐标到屏幕坐标
            start_pos = self._node_to_screen(source_node.position)
            end_pos = self._node_to_screen(target_node.position)
            
            # 检查是否是hover的边
            is_hovered = (
                self.hovered_edge and 
                (edge.source_id, edge.target_id) in [
                    self.hovered_edge,
                    (self.hovered_edge[1], self.hovered_edge[0])
                ]
            )
            
            # 绘制虚线
            if is_hovered:
                # hover时加粗并改变颜色
                color = arcade.color.YELLOW
                line_width = self.line_width * 1.5
            else:
                color = self.edge_color
                line_width = self.line_width
            
            self._draw_dashed_line(start_pos, end_pos, color, line_width)
    
    def _draw_nodes(self):
        """绘制所有节点"""
        for node in self.map_system.nodes.values():
            screen_pos = self._node_to_screen(node.position)
            
            # 确定节点颜色
            if node.is_current:
                # 当前节点：同心圆（金色外圈 + 白色内圈）
                outer_radius = self.hover_radius
                inner_radius = self.node_radius
                
                # 外圈
                arcade.draw_circle_filled(
                    screen_pos[0], screen_pos[1],
                    outer_radius,
                    self.current_node_color
                )
                
                # 内圈
                arcade.draw_circle_filled(
                    screen_pos[0], screen_pos[1],
                    inner_radius,
                    self.node_color
                )
            elif node == self.hovered_node:
                # hover节点：稍大的白色圆
                arcade.draw_circle_filled(
                    screen_pos[0], screen_pos[1],
                    self.hover_radius,
                    self.node_color
                )
            else:
                # 普通节点：白色圆
                arcade.draw_circle_filled(
                    screen_pos[0], screen_pos[1],
                    self.node_radius,
                    self.node_color
                )
    
    def _draw_dashed_line(self, start: Tuple[float, float], 
                         end: Tuple[float, float], 
                         color: Tuple[int, int, int], 
                         line_width: float):
        """绘制虚线"""
        dash_length = S.scale(10)
        gap_length = S.scale(5)
        
        # 计算线段长度和方向
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = ((dx ** 2) + (dy ** 2)) ** 0.5
        
        if length == 0:
            return
        
        # 单位向量
        unit_x = dx / length
        unit_y = dy / length
        
        # 绘制虚线
        current_dist = 0
        while current_dist < length:
            # 计算dash的起点和终点
            dash_start_x = start[0] + unit_x * current_dist
            dash_start_y = start[1] + unit_y * current_dist
            
            dash_end_dist = min(current_dist + dash_length, length)
            dash_end_x = start[0] + unit_x * dash_end_dist
            dash_end_y = start[1] + unit_y * dash_end_dist
            
            # 绘制dash
            arcade.draw_line(
                dash_start_x, dash_start_y,
                dash_end_x, dash_end_y,
                color, line_width
            )
            
            # 移动到下一个dash
            current_dist += dash_length + gap_length
    
    def _draw_tooltip(self):
        """绘制hover提示框"""
        if not self.hovered_node and not self.hovered_edge:
            return
        
        tooltip_text = []
        
        # 节点tooltip
        if self.hovered_node:
            node = self.hovered_node
            tooltip_text.append(f"节点: {node.name}")
            tooltip_text.append(f"类型: {node.node_type.value}")
            tooltip_text.append(f"描述: {node.description}")
            if node.is_visited:
                tooltip_text.append("✓ 已访问")
            if node.is_current:
                tooltip_text.append("★ 当前位置")
        
        # 边tooltip
        elif self.hovered_edge:
            edge = self.map_system.get_edge(*self.hovered_edge)
            if edge:
                source = self.map_system.nodes.get(edge.source_id)
                target = self.map_system.nodes.get(edge.target_id)
                if source and target:
                    tooltip_text.append(f"路径: {source.name} → {target.name}")
                    tooltip_text.append(f"移动成本: {edge.movement_cost}")
                    if edge.description:
                        tooltip_text.append(f"描述: {edge.description}")
        
        if not tooltip_text:
            return
        
        # 计算tooltip位置和大小
        padding = S.scale(10)
        line_height = S.font(16)
        text_width = max(len(line) for line in tooltip_text) * S.font(12)
        text_height = len(tooltip_text) * line_height + padding * 2
        
        # 设置tooltip位置（在鼠标附近）
        tooltip_x = self.tooltip_x + S.scale(15)
        tooltip_y = self.tooltip_y + S.scale(15)
        
        # 确保tooltip不超出屏幕
        if tooltip_x + text_width > self.window_width:
            tooltip_x = self.window_width - text_width - S.scale(10)
        if tooltip_y + text_height > self.window_height:
            tooltip_y = self.window_height - text_height - S.scale(10)
        
        # 绘制背景
        arcade.draw_lrbt_rectangle_filled(
            tooltip_x, tooltip_x + text_width,
            tooltip_y, tooltip_y + text_height,
            (50, 50, 50)  # 深灰色
        )
        
        # 绘制边框
        arcade.draw_lrbt_rectangle_outline(
            tooltip_x, tooltip_x + text_width,
            tooltip_y, tooltip_y + text_height,
            arcade.color.WHITE,
            S.scale(2)
        )
        
        # 绘制文字
        y_offset = tooltip_y + text_height - padding
        for line in tooltip_text:
            arcade.draw_text(
                line,
                tooltip_x + padding,
                y_offset,
                self.text_color,
                S.font(14),
                anchor_x="left",
                anchor_y="top"
            )
            y_offset -= line_height
    
    def _draw_ui_hints(self):
        """绘制UI提示信息"""
        hint_y = self.window_height - S.py(30)
        
        arcade.draw_text(
            "点击其他节点移动 | Hover查看信息 | ESC返回",
            self.window_width // 2,
            hint_y,
            arcade.color.YELLOW,
            S.font(18),
            anchor_x="center",
            anchor_y="center"
        )
    
    def _draw_resource_status(self):
        """绘制资源状态栏（左上角）"""
        # 获取资源管理器
        if not hasattr(self.map_system, 'resource_manager'):
            return
        
        resource_mgr = self.map_system.resource_manager
        status = resource_mgr.get_status_summary()
        
        # 左上角位置
        start_x = S.px(20)
        start_y = self.window_height - S.py(20)
        
        # 背景框尺寸
        box_width = S.px(280)
        box_height = S.py(80)
        
        # 绘制半透明背景
        arcade.draw_lrbt_rectangle_filled(
            start_x, start_x + box_width,
            start_y - box_height, start_y,
            (40, 40, 40, 220)  # 深灰色半透明
        )
        
        # 绘制边框
        arcade.draw_lrbt_rectangle_outline(
            start_x, start_x + box_width,
            start_y - box_height, start_y,
            arcade.color.GOLD,
            S.scale(2)
        )
        
        # 标题
        arcade.draw_text(
            "📦 资源状态",
            start_x + S.px(10),
            start_y - S.py(15),
            arcade.color.GOLD,
            S.font(16),
            anchor_x="left",
            anchor_y="top",
            bold=True
        )
        
        # 资源信息
        info_y = start_y - S.py(35)
        line_height = S.py(18)
        
        # 食物
        food_color = arcade.color.GREEN if self.map_system.player_resources.food_units > 5 else arcade.color.RED
        arcade.draw_text(
            f"🍞 食物: {status['food']}",
            start_x + S.px(15),
            info_y,
            food_color,
            S.font(14),
            anchor_x="left",
            anchor_y="top"
        )
        
        # 时间
        arcade.draw_text(
            f"⏰ 时间: {status['time']}",
            start_x + S.px(15),
            info_y - line_height,
            arcade.color.WHITE,
            S.font(14),
            anchor_x="left",
            anchor_y="top"
        )
        
        # 金币和幸运点
        arcade.draw_text(
            f"💰 金币: {status['gold']}  |  🍀 幸运: {status['luck']}",
            start_x + S.px(15),
            info_y - line_height * 2,
            arcade.color.WHITE,
            S.font(14),
            anchor_x="left",
            anchor_y="top"
        )
    
    def _node_to_screen(self, node_pos: Tuple[float, float]) -> Tuple[float, float]:
        """将节点逻辑坐标转换为屏幕坐标"""
        # 简单映射：假设节点坐标范围是 0-1000
        # 可以根据实际需要调整缩放和平移
        scale_x = self.window_width / 1000
        scale_y = self.window_height / 700
        
        screen_x = node_pos[0] * scale_x
        screen_y = node_pos[1] * scale_y
        
        return (screen_x, screen_y)
    
    def _screen_to_node_area(self, screen_x: float, screen_y: float) -> Optional[MapNode]:
        """根据屏幕坐标查找hover的节点"""
        for node in self.map_system.nodes.values():
            screen_pos = self._node_to_screen(node.position)
            
            # 计算距离
            distance = ((screen_pos[0] - screen_x) ** 2 + 
                       (screen_pos[1] - screen_y) ** 2) ** 0.5
            
            # 如果在节点范围内
            if distance <= self.hover_radius:
                return node
        
        return None
    
    def _screen_to_edge_area(self, screen_x: float, screen_y: float) -> Optional[Tuple[str, str]]:
        """根据屏幕坐标查找hover的边"""
        threshold = S.scale(10)  # 边的检测阈值
        
        for edge in self.map_system.edges.values():
            source_node = self.map_system.nodes.get(edge.source_id)
            target_node = self.map_system.nodes.get(edge.target_id)
            
            if not source_node or not target_node:
                continue
            
            start_pos = self._node_to_screen(source_node.position)
            end_pos = self._node_to_screen(target_node.position)
            
            # 计算点到线段的距离
            distance = self._point_to_line_distance(
                (screen_x, screen_y), start_pos, end_pos
            )
            
            if distance <= threshold:
                return (edge.source_id, edge.target_id)
        
        return None
    
    def _point_to_line_distance(self, point: Tuple[float, float],
                                line_start: Tuple[float, float],
                                line_end: Tuple[float, float]) -> float:
        """计算点到线段的最短距离"""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # 线段长度平方
        line_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        
        if line_len_sq == 0:
            # 线段是一个点
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        
        # 计算投影参数 t
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_len_sq))
        
        # 计算投影点
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        # 返回距离
        return ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5
    
    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """鼠标移动事件"""
        self.tooltip_x = x
        self.tooltip_y = y
        
        # 检查hover的节点
        self.hovered_node = self._screen_to_node_area(x, y)
        
        # 如果没有hover节点，检查hover的边
        if not self.hovered_node:
            self.hovered_edge = self._screen_to_edge_area(x, y)
        else:
            self.hovered_edge = None
    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """鼠标点击事件"""
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
        
        # 检查是否点击了节点
        clicked_node = self._screen_to_node_area(x, y)
        
        if clicked_node:
            # 如果点击的是当前节点，不做任何事
            if clicked_node.is_current:
                print(f"[地图] 已在节点: {clicked_node.name}")
                return
            
            # 如果是战斗节点，触发战斗
            if clicked_node.node_type == NodeType.BATTLE_ZONE:
                if self.player_entity:
                    success, message = self.battle_trigger.trigger_battle(
                        clicked_node, 
                        self.player_entity
                    )
                    if success:
                        print(f"[地图] {message}")
                        # 战斗会在回调中处理
                    else:
                        print(f"[地图] 无法触发战斗: {message}")
                else:
                    print("[地图] 警告：未设置玩家实体，无法触发战斗")
                return
            
            # 尝试移动到新节点
            success, message = self.map_system.move_to_node(clicked_node.node_id)
            
            if success:
                print(f"[地图] {message}")
            else:
                print(f"[地图] 无法移动: {message}")
    
    def on_key_press(self, key: int, modifiers: int):
        """键盘事件"""
        if key == arcade.key.ESCAPE:
            # ESC返回
            print("[地图] 返回主菜单")
            # TODO: 实现返回逻辑，暂时关闭窗口
            self.window.close()
        
        elif key == arcade.key.E:
            # E键切换装备栏显示
            self.show_equipment = not self.show_equipment
            self.show_inventory = False  # 互斥显示
            status = "显示" if self.show_equipment else "隐藏"
            print(f"[地图] {status}装备栏")
        
        elif key == arcade.key.I:
            # I键切换背包栏显示
            self.show_inventory = not self.show_inventory
            self.show_equipment = False  # 互斥显示
            status = "显示" if self.show_inventory else "隐藏"
            print(f"[地图] {status}背包栏")
        
        elif key == arcade.key.S:
            # S键保存游戏
            self.map_system.save_to_file("save.json")
            print("[地图] 游戏已保存")
    
    def on_update(self, delta_time: float):
        """更新逻辑"""
        pass

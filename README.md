# 卡牌战斗游戏 - Arcade 重构版

## 项目简介

这是一个使用 Python Arcade 引擎重构的回合制卡牌战斗游戏。原项目使用 Tkinter 开发，现已完全重构为更现代化、更易扩展的架构。

## 主要改进

### 1. 架构优化
- **模块化设计**：将代码拆分为多个独立模块（配置、模型、战斗系统、视图等）
- **数据驱动**：使用枚举和常量管理游戏数据
- **分离关注点**：逻辑层与表现层完全分离

### 2. 代码质量提升
- **类型安全**：使用 dataclass 和类型注解
- **面向对象**：清晰的类继承关系和职责划分
- **可扩展性**：易于添加新卡牌、装备和角色

### 3. 技术栈升级
- **Arcade 引擎**：替代 Tkinter，提供更好的图形性能和游戏体验
- **现代化 Python**：使用 Python 3.7+ 特性

### 4. 瓦片地图系统（新增）
- **固定棋盘格地图**：使用固定的两种绿色调交替模式，确保每次启动一致
- **可视化单位**：蓝色表示己方，红色表示敌方
- **移动系统**：支持点击移动和键盘控制（WASD/方向键）
- **卡牌攻击融合**：点击卡牌显示攻击范围，再点击目标位置使用卡牌
- **射程显示**：深色区域表示卡牌的有效攻击/移动范围
- **居中显示**：地图自动居中于屏幕中央

## 文件结构

```
PythonProject/
├── main.py              # 主程序入口
├── config.py            # 配置和常量定义
├── models.py            # 核心数据模型（实体、卡牌、装备等）
├── battle_system.py     # 战斗系统逻辑
├── card_database.py     # 卡牌、武器、防具数据库
├── card_serializer.py   # 卡牌序列化模块（新增）
├── tile_map.py          # 瓦片地图系统（新增）
├── game_view.py         # Arcade 视图和渲染
├── test_serialization.py    # 序列化测试脚本（新增）
├── test_tile_map.py         # 瓦片地图测试脚本（新增）
├── example_advanced_serialization.py  # 高级示例（新增）
├── SERIALIZATION_GUIDE.md       # 序列化使用指南（新增）
├── SERIALIZATION_QUICKREF.md    # 快速参考（新增）
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明
```

## 安装依赖

```bash
pip install -r requirements.txt
```

或直接安装：

```bash
pip install arcade
```

## 运行游戏

```bash
python main.py
```

## 游戏操作

### 基本操作
- **鼠标左键点击卡牌**：使用选中的卡牌
- **空格键**：跳过当前回合
- **ESC键**：退出游戏（战斗结束后）
- **鼠标悬停**：查看卡牌详细信息

### 瓦片地图操作（新增）
- **点击瓦片**：移动玩家到该位置
- **WASD/方向键**：控制玩家移动
- **点击卡牌**：选择卡牌并显示攻击范围（深色区域）
- **点击目标**：在范围内点击目标位置使用卡牌
- **蓝色圆圈**：己方单位
- **红色圆圈**：敌方单位
- **深色区域**：卡牌的有效攻击/移动范围

## 核心模块说明

### config.py
定义所有游戏常量和枚举类型：
- `Rarity`：稀有度枚举
- `CardType`：卡牌类型枚举
- `GameConstants`：游戏配置常量

### models.py
核心数据模型：
- `Entity`：游戏实体（玩家、敌人）
- `Card`：卡牌类
- `Weapon` / `Armor`：装备类
- `Stats`：角色属性
- `Buff`：增益/减益效果

### battle_system.py
战斗系统管理器：
- 回合制战斗逻辑
- AI 自动出牌
- Buff 处理
- 战斗状态管理

### card_database.py
游戏内容数据库：
- 所有可用卡牌定义
- 武器装备库
- 预设角色创建

### card_serializer.py （新增）
卡牌序列化模块：
- JSON序列化和反序列化
- 文件保存和加载
- 复杂条件和效果处理
- 详见 [SERIALIZATION_GUIDE.md](SERIALIZATION_GUIDE.md)

### game_view.py
Arcade 视图层：
- UI 渲染
- 用户输入处理
- 动画效果
- 瓦片地图显示和交互

### tile_map.py （新增）
瓦片地图系统：
- 随机地图生成（两种绿色调）
- 瓦片管理和坐标转换
- 移动范围计算
- 高亮显示功能

## 扩展指南

### 添加新卡牌

在 `card_database.py` 中添加：

```python
"new_card": Card(
    name="新卡牌名称",
    card_type=CardType.ATTACK_PHYSICAL,
    ap_cost=2,
    effects={"hp": -30},
    description="卡牌描述",
    rarity=Rarity.RARE
)
```

### 添加新装备

```python
"new_weapon": Weapon(
    name="武器名称",
    description="武器描述",
    rarity=Rarity.UNCOMMON,
    physical_bonus=15,
    magical_bonus=10
)
```

### 添加新角色

```python
def create_new_character():
    player = Entity(
        name="角色名",
        max_hp=250,
        max_ap=4,
        equipment={...},
        cards=[...],
        hand_size=5
    )
    return player
```

## 设计理念

1. **单一职责原则**：每个模块只负责一个功能领域
2. **开闭原则**：对扩展开放，对修改关闭
3. **依赖倒置**：高层模块不依赖低层模块的具体实现
4. **数据与逻辑分离**：游戏数据独立于业务逻辑

## 未来计划

- [x] **卡牌序列化系统** - 已完成！支持JSON格式保存和加载
- [x] **瓦片地图系统** - 已完成！支持随机地图、移动和目标选择
- [ ] 添加更多卡牌类型和效果
- [ ] 实现多角色队伍战斗
- [ ] 添加技能树系统
- [ ] 实现更智能的 AI
- [ ] 添加卡牌动画效果
- [ ] 实现持久化ID系统
- [ ] 添加网络同步功能
- [ ] 增加障碍物和地形效果
- [ ] 实现路径finding算法

## 与原版本对比

| 特性 | 原版 (Tkinter) | 新版 (Arcade) |
|------|----------------|---------------|
| 图形性能 | 一般 | 优秀 |
| 代码结构 | 单文件，耦合度高 | 模块化，低耦合 |
| 可扩展性 | 困难 | 容易 |
| 维护性 | 较差 | 良好 |
| 跨平台 | 是 | 是 |
| 动画支持 | 有限 | 强大 |

## 许可证

本项目仅供学习和娱乐使用。

## 致谢

感谢原项目的创意和基础代码，本次重构保留了核心玩法，同时大幅提升了代码质量和可维护性。

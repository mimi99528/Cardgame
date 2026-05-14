#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查存档文件内容"""

import json
import os

if os.path.exists("save.json"):
    with open("save.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("=" * 70)
    print("存档文件内容检查")
    print("=" * 70)
    print(f"当前节点: {data['current_node_id']}")
    print(f"节点数量: {len(data['nodes'])}")
    print(f"\n玩家资源:")
    for key, value in data["player_resources"].items():
        print(f"  - {key}: {value}")
    
    print(f"\n已清剿节点:")
    cleared_nodes = [n for n in data["nodes"] if n.get("is_cleared")]
    if cleared_nodes:
        for node in cleared_nodes:
            print(f"  - {node['name']} (类型: {node['node_type']})")
    else:
        print("  无")
    
    print("\n" + "=" * 70)
    print("✓ 存档文件格式正确！")
    print("=" * 70)
else:
    print("✗ save.json 文件不存在")

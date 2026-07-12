#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Database - 轻量级记忆检索系统
支持：关键词精确匹配、BM25模糊检索、向量相似度检索（可选）
"""

import re
import json
import math
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter


class MemoryDatabase:
    """记忆数据库 - 支持多种检索方式"""

    def __init__(self):
        self.memories: List[Dict] = []  # 原始记忆数据
        self.inverted_index: Dict[str, set] = {}  # 倒排索引: 词 -> 记忆ID集合
        self.idf: Dict[str, float] = {}  # IDF值
        self.doc_freq: Dict[str, int] = {}  # 文档频率
        self.doc_lengths: List[int] = []  # 各文档长度
        self.avg_doc_length: float = 0.0  # 平均文档长度
        self.total_docs: int = 0  # 总文档数

        # BM25参数
        self.k1 = 1.5  # 词频饱和参数
        self.b = 0.75  # 长度归一化参数

    # ==================== 数据加载 ====================

    def load_from_html(self, html_content: str) -> int:
        """从HTML内容中提取记忆"""
        # 找到所有记忆块
        id_pattern = r'<div id="[a-f0-9-]+" class="memories-list-item">'
        ids = list(re.finditer(id_pattern, html_content))

        memory_blocks = []
        for i, m in enumerate(ids):
            start = m.start()
            if i + 1 < len(ids):
                end = ids[i + 1].start()
            else:
                end = len(html_content)
            memory_blocks.append(html_content[start:end])

        # 提取每条记忆
        for idx, block in enumerate(memory_blocks):
            memory = self._extract_memory(block, idx + 1)
            self.memories.append(memory)

        self._build_index()
        return len(self.memories)

    def _extract_memory(self, block: str, idx: int) -> Dict:
        """从HTML块中提取单条记忆"""
        # 标题
        title_match = re.search(r'<span class="memories-list-item-title">(.*?)</span>', block)
        title = title_match.group(1) if title_match else f"记忆_{idx}"

        # UUID
        uuid_match = re.search(r'<div id="([a-f0-9-]+)"', block)
        uuid = uuid_match.group(1) if uuid_match else ""

        # 范围
        scope_match = re.search(
            r'<div class="memories-item-detail-header">范围</div>.*?<p class="memories-item-detail-inner">(.*?)</p>',
            block, re.DOTALL
        )
        scope = scope_match.group(1).strip() if scope_match else ""

        # 关键词
        keywords_match = re.search(
            r'<div class="memories-item-detail-header">关键词</div>.*?<p class="memories-item-detail-inner">(.*?)</p>',
            block, re.DOTALL
        )
        keywords_raw = keywords_match.group(1).strip() if keywords_match else ""
        keywords = [k.strip() for k in keywords_raw.split(',') if k.strip()]

        # 记忆内容
        content = ""
        if '记忆内容</div>' in block:
            content_part = block.split('记忆内容</div>')[1]
            p_match = re.search(
                r'<p class="memories-item-detail-inner[^"]*">(.*?)</p>\s*</div>',
                content_part, re.DOTALL
            )
            if p_match:
                content_html = p_match.group(1)
                content = self._clean_html(content_html)

        return {
            "id": idx,
            "uuid": uuid,
            "title": title,
            "scope": scope,
            "keywords": keywords,
            "keywords_raw": keywords_raw,
            "content": content,
            "full_text": f"{title} {' '.join(keywords)} {content}"
        }

    def _clean_html(self, html: str) -> str:
        """清理HTML标签"""
        # mermaid代码块
        mermaid_match = re.search(r'<pre><code class="language-mermaid">(.*?)</code></pre>', html, re.DOTALL)
        if mermaid_match:
            return f"```mermaid\n{mermaid_match.group(1).strip()}\n```"

        # 普通HTML
        text = html
        text = re.sub(r'<h2>(.*?)</h2>', r'## \1\n', text)
        text = re.sub(r'<h3>(.*?)</h3>', r'### \1\n', text)
        text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL)
        text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
        return text.strip()

    def add_memory(self, title: str, content: str, keywords: List[str] = None,
                   scope: str = "") -> int:
        """手动添加记忆"""
        memory = {
            "id": len(self.memories) + 1,
            "uuid": "",
            "title": title,
            "scope": scope,
            "keywords": keywords or [],
            "keywords_raw": ", ".join(keywords) if keywords else "",
            "content": content,
            "full_text": f"{title} {' '.join(keywords or [])} {content}"
        }
        self.memories.append(memory)
        self._build_index()  # 重新构建索引
        return memory["id"]

    # ==================== 索引构建 ====================

    def _tokenize(self, text: str) -> List[str]:
        """中文分词（简单实现：按字符+英文单词）"""
        # 提取英文单词
        words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', text.lower())
        # 中文字符
        chars = re.findall(r'[\u4e00-\u9fff]', text)
        return words + chars

    def _build_index(self):
        """构建倒排索引和BM25统计"""
        self.inverted_index = defaultdict(set)
        self.doc_freq = defaultdict(int)
        self.doc_lengths = []
        self.total_docs = len(self.memories)

        if self.total_docs == 0:
            return

        for memory in self.memories:
            tokens = self._tokenize(memory["full_text"])
            self.doc_lengths.append(len(tokens))

            # 记录词频
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.inverted_index[token].add(memory["id"])
                self.doc_freq[token] += 1

        # 计算IDF
        self.idf = {}
        for token, df in self.doc_freq.items():
            # BM25 IDF
            self.idf[token] = math.log(
                (self.total_docs - df + 0.5) / (df + 0.5) + 1
            )

        self.avg_doc_length = sum(self.doc_lengths) / self.total_docs

    # ==================== 检索方法 ====================

    def search_keywords(self, keywords: List[str]) -> List[Dict]:
        """关键词精确匹配（AND逻辑）"""
        if not keywords:
            return []

        result_ids = None
        for kw in keywords:
            tokens = self._tokenize(kw)
            ids_for_kw = set()
            for token in tokens:
                ids_for_kw |= self.inverted_index.get(token, set())

            if result_ids is None:
                result_ids = ids_for_kw
            else:
                result_ids &= ids_for_kw  # 交集

        return [self.memories[i - 1] for i in (result_ids or [])]

    def search_bm25(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """BM25相关性检索"""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = {}
        for memory in self.memories:
            mid = memory["id"]
            score = 0.0

            for token in query_tokens:
                if token not in self.inverted_index:
                    continue

                # 计算TF
                doc_tokens = self._tokenize(memory["full_text"])
                tf = doc_tokens.count(token)

                # BM25公式
                doc_len = self.doc_lengths[mid - 1]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                score += self.idf.get(token, 0) * numerator / denominator

            if score > 0:
                scores[mid] = score

        # 排序返回
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(self.memories[i - 1], score) for i, score in sorted_results[:top_k]]

    def search_fuzzy(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """模糊检索：结合关键词匹配和BM25"""
        # 先尝试精确关键词匹配
        exact = self.search_keywords([query])
        if exact:
            return [(m, 1.0) for m in exact]

        # 否则用BM25
        return self.search_bm25(query, top_k)

    def search_by_title(self, title_pattern: str) -> List[Dict]:
        """按标题正则匹配"""
        pattern = re.compile(title_pattern, re.IGNORECASE)
        return [m for m in self.memories if pattern.search(m["title"])]

    def get_memory(self, memory_id: int) -> Optional[Dict]:
        """按ID获取记忆"""
        for m in self.memories:
            if m["id"] == memory_id:
                return m
        return None

    # ==================== 持久化 ====================

    def save(self, filepath: str):
        """保存数据库到文件"""
        data = {
            "memories": self.memories,
            "inverted_index": {k: list(v) for k, v in self.inverted_index.items()},
            "idf": self.idf,
            "doc_freq": self.doc_freq,
            "doc_lengths": self.doc_lengths,
            "avg_doc_length": self.avg_doc_length,
            "total_docs": self.total_docs
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"数据库已保存到: {filepath}")

    def load(self, filepath: str):
        """从文件加载数据库"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.memories = data["memories"]
        self.inverted_index = {k: set(v) for k, v in data["inverted_index"].items()}
        self.idf = data["idf"]
        self.doc_freq = data["doc_freq"]
        self.doc_lengths = data["doc_lengths"]
        self.avg_doc_length = data["avg_doc_length"]
        self.total_docs = data["total_docs"]
        print(f"数据库已从 {filepath} 加载，共 {self.total_docs} 条记忆")

    def export_json(self, filepath: str):
        """导出为JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
        print(f"已导出到: {filepath}")

    # ==================== 展示 ====================

    def list_all(self):
        """列出所有记忆"""
        print(f"\n{'=' * 70}")
        print(f"记忆数据库 - 共 {len(self.memories)} 条")
        print(f"{'=' * 70}")
        for m in self.memories:
            print(f"\n[{m['id']}] {m['title']}")
            print(f"    关键词: {', '.join(m['keywords'])}")
            print(f"    内容预览: {m['content'][:80]}...")

    def show_memory(self, memory_id: int):
        """详细展示单条记忆"""
        m = self.get_memory(memory_id)
        if not m:
            print(f"未找到记忆 ID={memory_id}")
            return

        print(f"\n{'=' * 70}")
        print(f"[{m['id']}] {m['title']}")
        print(f"{'=' * 70}")
        print(f"UUID: {m['uuid']}")
        print(f"范围: {m['scope']}")
        print(f"关键词: {', '.join(m['keywords'])}")
        print(f"\n内容:\n{m['content']}")
        print(f"{'=' * 70}")


# ==================== 使用示例 ====================

def main():
    db = MemoryDatabase()

    # 1. 从HTML文件加载（你的实际数据）
    html_file = Path(r"C:\Users\ADMIN\Desktop\memory.txt")
    html_content = html_file.read_text(encoding='utf-8')
    count = db.load_from_html(html_content)
    print(f"成功加载 {count} 条记忆")

    # 2. 手动添加示例记忆（演示用）
#     db.add_memory(
#         title="AI出牌间隔配置",
#         content="AI控制角色出牌间隔为0.5秒，该间隔时间可通过配置修改，避免AI一次性打出所有卡牌。",
#         keywords=["AI出牌", "间隔时间", "可配置"],
#         scope="D:\\PythonProject\\PythonProject"
#     )
#
#     db.add_memory(
#         title="瓦片地图系统添加任务流程",
#         content="""```mermaid
# graph TD
#     A[需求: 新增瓦片地图系统] --> B[分析项目结构]
#     B --> C[创建tile_map.py模块]
#     C --> D[在game_view.py中集成地图]
#     D --> E[实现鼠标与键盘交互逻辑]
#     E --> F[添加测试脚本验证功能]
#     F --> G[更新README文档说明新功能]
# ```""",
#         keywords=["瓦片地图", "系统添加", "任务流程"],
#         scope="D:\\PythonProject\\PythonProject"
#     )
#
#     db.add_memory(
#         title="Arcade游戏血条绘制与文本性能优化流程",
#         content="""```mermaid
# graph TD
#     A[接收任务:修复血条坐标错误和性能警告] --> B[分析错误原因]
#     B --> C{问题类型}
#     C --> D[ValueError: left > right 坐标错误]
#     C --> E[PerformanceWarning: draw_text性能问题]
#     D --> F[在_draw_battle_info中添加left <= right校验]
#     E --> G[实现_text_objects缓存机制]
#     G --> H[使用arcade.Text替代draw_text]
#     H --> I[修正Text对象x/y参数名]
#     I --> J[创建_draw_text辅助方法支持Text对象]
#     J --> K[实现Text对象回退机制确保稳定性]
#     J --> L[运行测试并处理multiline参数兼容性]
#     J --> M[调整UI布局参数避免元素重叠]
#     J --> N[添加缓存清理机制防止内存泄漏]
#     N --> O[测试验证修复效果]
#     O --> P[确认无错误无警告]
# ```""",
#         keywords=["Arcade", "性能优化", "draw_text", "UI布局", "缓存机制"],
#         scope="D:\\PythonProject\\PythonProject"
#     )
#
#     db.add_memory(
#         title="Arcade纹理绘制使用draw_texture_rect而非draw_texture_rectangle",
#         content="在Arcade 3.3.3版本中，不存在`arcade.draw_texture_rectangle`函数，正确的方法是使用`arcade.draw_texture_rect(texture, arcade.XYWH(x, y, width, height))`来绘制纹理。若继续使用已移除的方法将导致AttributeError。（来源：run_in_terminal执行python脚本报错）",
#         keywords=["Arcade", "draw_texture_rect", "纹理绘制", "API变更"],
#         scope="D:\\PythonProject\\PythonProject"
#     )
#
#     db.add_memory(
#         title="Arcade坐标系陷阱-左下角原点y轴向上",
#         content="""## 错误原因
# 在Arcade框架中使用了错误的坐标系理解，误以为y值越小位置越靠上，导致战斗日志等UI元素定位错误。
#
# ## 解决方案
# Arcade使用左下角为原点的坐标系（y轴向上），即y值越大，位置越靠上。UI元素的y坐标应基于`window_height - element_height - offset`的方式从上往下布局。
#
# ## 来源工具
# search_replace（修改game_view.py中的坐标计算逻辑）""",
#         keywords=["Arcade坐标系", "y轴方向", "UI布局", "原点位置"],
#         scope="D:\\PythonProject\\PythonProject"
#     )

    # 展示所有记忆
    db.list_all()

    # ==================== 检索演示 ====================

    print(f"\n{'=' * 70}")
    print("检索演示")
    print(f"{'=' * 70}")

    # 1. 关键词精确匹配
    print("\n--- 关键词检索: 'Arcade' ---")
    results = db.search_keywords(["Arcade"])
    for r in results:
        print(f"  ✓ [{r['id']}] {r['title']}")

    # 2. BM25模糊检索
    print("\n--- BM25检索: '坐标系错误怎么解决' ---")
    results = db.search_bm25("坐标系错误怎么解决", top_k=3)
    for r, score in results:
        print(f"  ✓ [{r['id']}] {r['title']} (score: {score:.3f})")

    print("\n--- BM25检索: '纹理绘制API' ---")
    results = db.search_bm25("纹理绘制API", top_k=3)
    for r, score in results:
        print(f"  ✓ [{r['id']}] {r['title']} (score: {score:.3f})")

    print("\n--- BM25检索: '性能优化缓存' ---")
    results = db.search_bm25("性能优化缓存", top_k=3)
    for r, score in results:
        print(f"  ✓ [{r['id']}] {r['title']} (score: {score:.3f})")

    # 3. 标题正则匹配
    print("\n--- 标题正则检索: 'Arcade.*坐标' ---")
    results = db.search_by_title(r'Arcade.*坐标')
    for r in results:
        print(f"  ✓ [{r['id']}] {r['title']}")

    # 4. 展示详细内容
    print("\n--- 查看记忆详情 ---")
    db.show_memory(129)

    # 保存数据库
    db.save("memory_db.pkl")
    db.export_json("memory_db.json")


if __name__ == "__main__":
    main()
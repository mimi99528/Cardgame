#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Vector Database - 自包含向量记忆检索系统
基于 TF-IDF + 字符 n-gram 向量化 + 余弦相似度，无需任何外部模型下载
支持语义检索、关键词检索、动态增删
"""

import re
import json
import math
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from collections import defaultdict

import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial.distance import cdist


# ==================== 分词工具 ====================

def tokenize(text: str, ngram_range: Tuple[int, int] = (1, 3)) -> List[str]:
    """中文混合分词：英文单词 + 中文字符 n-gram"""
    tokens = []
    text_lower = text.lower()

    # 提取英文单词（连续字母数字）
    for m in re.finditer(r'[a-zA-Z_][a-zA-Z0-9_]{1,}', text_lower):
        tokens.append(m.group())

    # 提取中文字符序列，生成 n-gram
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    for n in range(ngram_range[0], ngram_range[1] + 1):
        for i in range(len(chinese_chars) - n + 1):
            tokens.append(''.join(chinese_chars[i:i + n]))

    # 数字序列
    for m in re.finditer(r'\d+', text):
        tokens.append(m.group())

    return tokens


# ==================== TF-IDF 向量化器 ====================

class TfidfVectorizer:
    """轻量 TF-IDF 向量化器，支持增量更新"""

    def __init__(self, ngram_range: Tuple[int, int] = (1, 3), max_features: int = 5000):
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.vocabulary: Dict[str, int] = {}       # word -> index
        self.idf: np.ndarray = np.array([])
        self.doc_count: int = 0
        self._df: Dict[int, int] = defaultdict(int)  # document frequency

    def _build_vocab(self, all_tokens_list: List[List[str]]):
        """从所有文档构建词汇表"""
        df = defaultdict(int)
        for tokens in all_tokens_list:
            for token in set(tokens):
                df[token] += 1

        # 按文档频率排序，取 top max_features
        sorted_terms = sorted(df.items(), key=lambda x: x[1], reverse=True)
        if self.max_features:
            sorted_terms = sorted_terms[:self.max_features]

        self.vocabulary = {term: idx for idx, (term, _) in enumerate(sorted_terms)}
        self._df = {idx: df[term] for term, idx in self.vocabulary.items()}

    def fit(self, documents: List[str]):
        """首次拟合"""
        all_tokens = [tokenize(doc, self.ngram_range) for doc in documents]
        self.doc_count = len(documents)
        self._build_vocab(all_tokens)
        self._compute_idf()
        return self.transform(documents)

    def _compute_idf(self):
        """计算 IDF"""
        if not self.vocabulary:
            return
        n = max(self.doc_count, 1)
        self.idf = np.zeros(len(self.vocabulary))
        for idx, df in self._df.items():
            self.idf[idx] = math.log((n - df + 0.5) / (df + 0.5) + 1)

    def transform(self, documents: List[str]) -> csr_matrix:
        """将文档转为 TF-IDF 稀疏矩阵"""
        if not self.vocabulary:
            return csr_matrix((len(documents), 0))

        rows, cols, data = [], [], []
        for i, doc in enumerate(documents):
            tokens = tokenize(doc, self.ngram_range)
            tf = defaultdict(float)
            for token in tokens:
                if token in self.vocabulary:
                    tf[self.vocabulary[token]] += 1

            # L2 normalize per document
            norm = math.sqrt(sum(v * v for v in tf.values())) or 1.0
            for idx, count in tf.items():
                rows.append(i)
                cols.append(idx)
                data.append((count / norm) * self.idf[idx])

        return csr_matrix((data, (rows, cols)),
                          shape=(len(documents), len(self.vocabulary)))

    def transform_query(self, query: str) -> np.ndarray:
        """查询文本向量化（不存储，直接返回 dense vector）"""
        if not self.vocabulary:
            return np.array([])

        vec = np.zeros(len(self.vocabulary))
        tokens = tokenize(query, self.ngram_range)
        tf = defaultdict(float)
        for token in tokens:
            if token in self.vocabulary:
                tf[self.vocabulary[token]] += 1

        norm = math.sqrt(sum(v * v for v in tf.values())) or 1.0
        for idx, count in tf.items():
            vec[idx] = (count / norm) * self.idf[idx]

        return vec

    def add_document(self, document: str) -> csr_matrix:
        """增量添加一篇文档，更新词汇表和 IDF"""
        tokens = tokenize(document, self.ngram_range)
        new_terms = set(tokens) - set(self.vocabulary.keys())

        # 为新词分配索引
        for term in new_terms:
            if self.max_features and len(self.vocabulary) >= self.max_features:
                break
            self.vocabulary[term] = len(self.vocabulary)

        self.doc_count += 1
        for term in set(tokens):
            if term in self.vocabulary:
                self._df[self.vocabulary[term]] = self._df.get(self.vocabulary[term], 0) + 1

        self._compute_idf()
        return self.transform([document])

    def remove_document(self, doc_index: int = None):
        """标记删除（IDF 需要重建，调用 rebuild 后生效）"""
        self.doc_count = max(self.doc_count - 1, 0)

    def rebuild(self, documents: List[str]):
        """完全重建词汇表和 IDF"""
        self.vocabulary.clear()
        self._df.clear()
        all_tokens = [tokenize(doc, self.ngram_range) for doc in documents]
        self.doc_count = len(documents)
        self._build_vocab(all_tokens)
        self._compute_idf()


# ==================== 向量记忆数据库 ====================

class MemoryVectorDB:
    """向量记忆数据库"""

    def __init__(self, persist_dir: str = "./memory_vectordb"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.memories: List[Dict] = []
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=5000)
        self.vectors: csr_matrix = csr_matrix((0, 0))
        self._id_counter: int = 0

        # 尝试从已有数据加载
        if self._has_saved_data():
            self.load()

    # ==================== ID 管理 ====================

    def _next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    # ==================== CRUD ====================

    def add_memory(
        self,
        title: str,
        content: str,
        keywords: List[str] = None,
        scope: str = "",
    ) -> int:
        """添加记忆，返回 ID"""
        keywords = keywords or []
        full_text = self._build_full_text(title, content, keywords)

        mid = self._next_id()
        memory = {
            "id": mid,
            "title": title,
            "scope": scope,
            "keywords": keywords,
            "content": content,
            "full_text": full_text,
        }
        self.memories.append(memory)

        # 更新向量
        all_texts = [m["full_text"] for m in self.memories]
        self.vectorizer.rebuild(all_texts)
        self.vectors = self.vectorizer.transform(all_texts)

        self._auto_save()
        return mid

    def delete_memory(self, memory_id: int) -> Optional[Dict]:
        """删除记忆，返回被删除的记忆（供确认用）"""
        idx = self._find_index(memory_id)
        if idx is None:
            return None

        removed = self.memories.pop(idx)

        # 重建向量索引
        if self.memories:
            all_texts = [m["full_text"] for m in self.memories]
            self.vectorizer.rebuild(all_texts)
            self.vectors = self.vectorizer.transform(all_texts)
        else:
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=5000)
            self.vectors = csr_matrix((0, 0))

        self._auto_save()
        return removed

    def get_memory(self, memory_id: int) -> Optional[Dict]:
        """按 ID 获取记忆"""
        idx = self._find_index(memory_id)
        return self.memories[idx] if idx is not None else None

    def update_memory(
        self,
        memory_id: int,
        title: str = None,
        content: str = None,
        keywords: List[str] = None,
    ) -> bool:
        """更新记忆"""
        idx = self._find_index(memory_id)
        if idx is None:
            return False

        m = self.memories[idx]
        new_title = title if title is not None else m["title"]
        new_content = content if content is not None else m["content"]
        new_keywords = keywords if keywords is not None else m["keywords"]

        m["title"] = new_title
        m["content"] = new_content
        m["keywords"] = new_keywords
        m["full_text"] = self._build_full_text(new_title, new_content, new_keywords)

        # 重建向量
        all_texts = [m["full_text"] for m in self.memories]
        self.vectorizer.rebuild(all_texts)
        self.vectors = self.vectorizer.transform(all_texts)

        self._auto_save()
        return True

    # ==================== 检索 ====================

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[Dict, float]]:
        """向量语义检索（TF-IDF + 余弦相似度）"""
        if not self.memories:
            return []

        query_vec = self.vectorizer.transform_query(query)
        if query_vec.sum() == 0:
            return []

        # 余弦相似度
        similarities = self.vectors.dot(query_vec)
        # 文档 L2 范数
        doc_norms = np.sqrt(self.vectors.power(2).sum(axis=1)).A1
        query_norm = np.linalg.norm(query_vec)

        scores = []
        for i, sim in enumerate(similarities):
            denom = doc_norms[i] * query_norm
            if denom > 0:
                score = sim / denom
                if score >= threshold:
                    scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [(dict(self.memories[i]), round(score, 4)) for i, score in scores[:top_k]]

    def search_keywords(self, keywords: List[str]) -> List[Dict]:
        """关键词包含匹配（AND 逻辑）"""
        if not keywords:
            return []
        results = []
        for m in self.memories:
            text = f"{m['title']} {m['content']} {', '.join(m['keywords'])}"
            if all(kw.lower() in text.lower() for kw in keywords):
                results.append(dict(m))
        return results

    def search_by_title(self, pattern: str) -> List[Dict]:
        """正则标题匹配"""
        pat = re.compile(pattern, re.IGNORECASE)
        return [dict(m) for m in self.memories if pat.search(m["title"])]

    # ==================== HTML 导入 ====================

    def load_from_html(self, html_content: str) -> int:
        """从 HTML 文件批量导入记忆"""
        id_pattern = r'<div id="[a-f0-9-]+" class="memories-list-item">'
        ids = list(re.finditer(id_pattern, html_content))

        memory_blocks = []
        for i, m in enumerate(ids):
            start = m.start()
            end = ids[i + 1].start() if i + 1 < len(ids) else len(html_content)
            memory_blocks.append(html_content[start:end])

        count = 0
        for block in memory_blocks:
            mem = self._extract_memory(block)
            self.add_memory(
                title=mem["title"],
                content=mem["content"],
                keywords=mem["keywords"],
                scope=mem["scope"],
            )
            count += 1

        return count

    def _extract_memory(self, block: str) -> Dict:
        """从 HTML 块提取记忆"""
        title_match = re.search(r'<span class="memories-list-item-title">(.*?)</span>', block)
        title = title_match.group(1) if title_match else "未命名"

        scope_match = re.search(
            r'<div class="memories-item-detail-header">范围</div>.*?<p class="memories-item-detail-inner">(.*?)</p>',
            block, re.DOTALL,
        )
        scope = scope_match.group(1).strip() if scope_match else ""

        keywords_match = re.search(
            r'<div class="memories-item-detail-header">关键词</div>.*?<p class="memories-item-detail-inner">(.*?)</p>',
            block, re.DOTALL,
        )
        keywords_raw = keywords_match.group(1).strip() if keywords_match else ""
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

        content = ""
        if "记忆内容</div>" in block:
            content_part = block.split("记忆内容</div>")[1]
            p_match = re.search(
                r'<p class="memories-item-detail-inner[^"]*">(.*?)</p>\s*</div>',
                content_part, re.DOTALL,
            )
            if p_match:
                content = self._clean_html(p_match.group(1))

        return {"title": title, "scope": scope, "keywords": keywords, "content": content}

    @staticmethod
    def _clean_html(html: str) -> str:
        text = html
        text = re.sub(r'<h2>(.*?)</h2>', r'## \1\n', text)
        text = re.sub(r'<h3>(.*?)</h3>', r'### \1\n', text)
        text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL)
        text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
        return text.strip()

    # ==================== 持久化 ====================

    def _has_saved_data(self) -> bool:
        return (self.persist_dir / "memories.json").exists()

    def _auto_save(self):
        """每次增删改后自动保存"""
        self._save_memories()

    def _save_memories(self):
        """保存记忆和向量化器状态"""
        data = {
            "memories": self.memories,
            "id_counter": self._id_counter,
            "vocabulary": self.vectorizer.vocabulary,
            "df": dict(self.vectorizer._df),
            "idf": self.vectorizer.idf.tolist() if len(self.vectorizer.idf) > 0 else [],
            "doc_count": self.vectorizer.doc_count,
        }
        with open(self.persist_dir / "memories.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save(self):
        """手动保存"""
        self._save_memories()
        print(f"数据库已保存到: {self.persist_dir}")

    def load(self):
        """从文件加载"""
        data_path = self.persist_dir / "memories.json"
        if not data_path.exists():
            return

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.memories = data.get("memories", [])
        self._id_counter = data.get("id_counter", len(self.memories))

        # 恢复向量化器
        vocab = data.get("vocabulary", {})
        self.vectorizer.vocabulary = vocab
        self.vectorizer._df = defaultdict(int, {int(k): v for k, v in data.get("df", {}).items()})
        self.vectorizer.idf = np.array(data.get("idf", []))
        self.vectorizer.doc_count = data.get("doc_count", len(self.memories))

        # 重建向量矩阵
        if self.memories:
            all_texts = [m["full_text"] for m in self.memories]
            self.vectors = self.vectorizer.transform(all_texts)

        print(f"已从 {data_path} 加载 {len(self.memories)} 条记忆")

    def export_json(self, filepath: str):
        """导出为 JSON"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
        print(f"已导出到: {filepath}")

    # ==================== 工具方法 ====================

    def _find_index(self, memory_id: int) -> Optional[int]:
        for i, m in enumerate(self.memories):
            if m["id"] == memory_id:
                return i
        return None

    @staticmethod
    def _build_full_text(title: str, content: str, keywords: List[str]) -> str:
        return f"{title} {' '.join(keywords)} {content}"

    def count(self) -> int:
        return len(self.memories)

    def list_all(self) -> List[Dict]:
        return [dict(m) for m in self.memories]

    # ==================== 展示 ====================

    def show_memory(self, memory_id: int):
        m = self.get_memory(memory_id)
        if not m:
            print(f"未找到记忆 ID={memory_id}")
            return
        print(f"\n{'=' * 70}")
        print(f"[{m['id']}] {m['title']}")
        print(f"{'=' * 70}")
        print(f"范围: {m['scope']}")
        print(f"关键词: {', '.join(m['keywords'])}")
        print(f"\n内容:\n{m['content']}")
        print(f"{'=' * 70}")

    def print_list(self):
        print(f"\n{'=' * 70}")
        print(f"向量记忆数据库 - 共 {self.count()} 条")
        print(f"{'=' * 70}")
        for m in self.memories:
            preview = m["content"][:80].replace("\n", " ")
            print(f"\n[{m['id']}] {m['title']}")
            print(f"    关键词: {', '.join(m['keywords'])}")
            print(f"    {preview}...")


# ==================== 使用示例 ====================

def main():
    db = MemoryVectorDB()

    html_file = Path(r"C:\Users\ADMIN\Desktop\memory.txt")
    if html_file.exists():
        html_content = html_file.read_text(encoding="utf-8")
        count = db.load_from_html(html_content)
        print(f"成功导入 {count} 条记忆")

    print("\n--- 语义检索: '坐标系错误怎么解决' ---")
    for mem, score in db.search("坐标系错误怎么解决", top_k=3):
        print(f"  [{mem['id']}] {mem['title']} (相似度: {score:.3f})")

    print("\n--- 语义检索: '纹理绘制API' ---")
    for mem, score in db.search("纹理绘制API", top_k=3):
        print(f"  [{mem['id']}] {mem['title']} (相似度: {score:.3f})")

    db.print_list()


if __name__ == "__main__":
    main()

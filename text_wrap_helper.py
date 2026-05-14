"""
中文文本换行辅助工具

提供多种方案来解决 Arcade 中文文本无法自动换行的问题
"""


def add_zero_width_spaces(text: str, interval: int = 2) -> str:
    """
    在中文文本中每隔指定字符数插入零宽空格（U+200B）
    
    Args:
        text: 原始中文文本
        interval: 插入间隔（每几个字符插入一个零宽空格）
        
    Returns:
        添加了零宽空格的文本
        
    Example:
        >>> add_zero_width_spaces("这是一段测试文本", 2)
        "这是\u200b一段\u200b测试\u200b文本"
    """
    if not text or interval <= 0:
        return text
    
    result = []
    for i, char in enumerate(text):
        result.append(char)
        # 每隔 interval 个字符插入零宽空格（不在末尾插入）
        if (i + 1) % interval == 0 and i < len(text) - 1:
            result.append('\u200b')
    
    return ''.join(result)


def wrap_chinese_text_smart(text: str, max_width: int, font_size: int = 16) -> str:
    """
    智能地为中文文本添加换行符
    
    策略：
    1. 保留已有的 \n 换行符
    2. 对于超长段落，按标点符号或固定长度插入 \n
    
    Args:
        text: 原始文本
        max_width: 最大宽度（像素）
        font_size: 字体大小
        
    Returns:
        添加了换行符的文本
    """
    # 估算每行可容纳的字符数
    chars_per_line = max_width // font_size
    
    if chars_per_line <= 0:
        return text
    
    # 按已有换行符分割
    paragraphs = text.split('\n')
    wrapped_paragraphs = []
    
    for paragraph in paragraphs:
        if len(paragraph) <= chars_per_line:
            wrapped_paragraphs.append(paragraph)
        else:
            # 超长段落，尝试在标点符号处换行
            wrapped_lines = []
            current_line = ""
            
            # 中文标点符号可以作为换行点
            break_points = '，。！？、；：,.!?;: '
            
            for char in paragraph:
                current_line += char
                
                # 如果达到宽度限制且当前字符是标点符号
                if len(current_line) >= chars_per_line and char in break_points:
                    wrapped_lines.append(current_line)
                    current_line = ""
            
            # 处理剩余文本
            if current_line:
                # 如果还有剩余，强制按长度分割
                while len(current_line) > chars_per_line:
                    wrapped_lines.append(current_line[:chars_per_line])
                    current_line = current_line[chars_per_line:]
                if current_line:
                    wrapped_lines.append(current_line)
            
            wrapped_paragraphs.extend(wrapped_lines)
    
    return '\n'.join(wrapped_paragraphs)


# 测试
if __name__ == "__main__":
    test_text = (
        "这是一段很长的中文测试文本用来验证自动换行功能是否能够正常工作。"
        "如果功能正常，这段文字应该会被自动分成多行显示。"
        "这是第二段，同样很长，需要继续换行。"
    )
    
    print("=" * 60)
    print("原始文本:")
    print(test_text)
    print()
    
    # 方案1：零宽空格
    zws_text = add_zero_width_spaces(test_text, interval=2)
    print("方案1 - 零宽空格 (interval=2):")
    print(zws_text)
    print(f"长度: {len(test_text)} -> {len(zws_text)}")
    print()
    
    # 方案2：智能换行
    wrapped_text = wrap_chinese_text_smart(test_text, max_width=300, font_size=16)
    print("方案2 - 智能换行 (max_width=300, font_size=16):")
    print(wrapped_text)
    print(f"行数: {len(wrapped_text.split(chr(10)))}")
    print()
    
    # 方案3：两者结合
    combined = wrap_chinese_text_smart(zws_text, max_width=300, font_size=16)
    print("方案3 - 零宽空格 + 智能换行:")
    print(combined)
    print()
    print("=" * 60)

"""
中文文本 ZWSP（零宽空格）换行辅助工具

在中文文本中自动插入零宽空格（U+200B），使 Arcade 能够正确换行
"""


def insert_zwsp_for_wrap(text: str, interval: int = 2) -> str:
    """
    在中文文本中每隔指定字符数插入零宽空格（ZWSP, U+200B）
    
    这是解决 Arcade 中文文本无法自动换行的最佳方案。
    零宽空格不会显示，但会被 Arcade 识别为换行点。
    
    Args:
        text: 原始中文文本
        interval: 插入间隔（每几个字符插入一个 ZWSP），默认 2
        
    Returns:
        插入了 ZWSP 的文本
        
    Examples:
        >>> insert_zwsp_for_wrap("这是一段测试文本", 2)
        "这是​一段​测试​文本"
        
        >>> insert_zwsp_for_wrap("Hello World", 3)
        "Hel​lo ​Wor​ld"
    """
    if not text or interval <= 0:
        return text
    
    result = []
    char_count = 0
    
    for char in text:
        result.append(char)
        char_count += 1
        
        # 每隔 interval 个字符插入 ZWSP（不在末尾插入）
        if char_count % interval == 0 and char != '\n':
            # 如果后面还有非换行符字符，才插入 ZWSP
            result.append('\u200b')
    
    return ''.join(result)


def prepare_text_for_arcade(text: str, max_width: int = None, font_size: int = 16, 
                           zws_interval: int = 2) -> str:
    """
    为 Arcade 绘制准备中文文本（推荐使用此函数）
    
    功能：
    1. 保留已有的 \n 换行符
    2. 在超长段落中自动插入 ZWSP 以支持换行
    3. 可根据 max_width 智能调整 ZWSP 间隔
    
    Args:
        text: 原始文本
        max_width: 最大宽度（像素），如果提供则自动计算最佳 interval
        font_size: 字体大小
        zws_interval: ZWSP 插入间隔（每几个字符插入一个）
        
    Returns:
        处理后的文本，可直接用于 arcade.Text 或 arcade.draw_text
        
    Examples:
        # 简单用法：固定间隔
        text = prepare_text_for_arcade("很长的中文文本", zws_interval=2)
        
        # 智能用法：根据宽度自动调整
        text = prepare_text_for_arcade("很长的中文文本", max_width=300, font_size=16)
    """
    if not text:
        return text
    
    # 如果提供了 max_width，智能计算 interval
    if max_width and max_width > 0:
        # 估算每行可容纳的字符数
        chars_per_line = max_width // font_size
        # ZWSP 间隔设为每行字符数的 1/3 到 1/2，平衡换行灵活性和性能
        calculated_interval = max(2, min(chars_per_line // 3, 4))
        zws_interval = calculated_interval
    
    # 按已有换行符分割，分别处理每一段
    paragraphs = text.split('\n')
    processed_paragraphs = []
    
    for paragraph in paragraphs:
        if paragraph:  # 跳过空行
            processed_paragraphs.append(insert_zwsp_for_wrap(paragraph, zws_interval))
        else:
            processed_paragraphs.append('')
    
    return '\n'.join(processed_paragraphs)


# 便捷别名
zwsp = '\u200b'  # 零宽空格常量


# 测试
if __name__ == "__main__":
    test_cases = [
        "这是一段很长的中文测试文本用来验证自动换行功能",
        "短文本",
        "包含\n换行符\n的文本",
        "Mixed English 和中文混合文本测试",
        "标点符号，测试。问号？感叹号！",
    ]
    
    print("=" * 70)
    print("ZWSP 中文换行辅助函数测试")
    print("=" * 70)
    print()
    
    for i, text in enumerate(test_cases, 1):
        print(f"测试 {i}:")
        print(f"  原始: {text}")
        
        # 方案1：固定间隔
        result1 = insert_zwsp_for_wrap(text, interval=2)
        print(f"  ZWSP(interval=2): {result1}")
        print(f"  长度变化: {len(text)} -> {len(result1)}")
        
        # 方案2：智能处理
        result2 = prepare_text_for_arcade(text, max_width=300, font_size=16)
        print(f"  智能处理(max_width=300): {result2}")
        
        print()
    
    print("=" * 70)
    print("使用示例:")
    print("=" * 70)
    print("""
# 在叙事渲染器中使用
from chinese_text_helper import prepare_text_for_arcade

# 准备文本
description = prepare_text_for_arcade(
    node.description,
    max_width=desc_width,
    font_size=self.description_font_size
)

# 绘制
desc_text = arcade.Text(
    description,
    desc_x, desc_y,
    arcade.color.WHITE,
    self.description_font_size,
    anchor_x="left",
    anchor_y="top",
    multiline=True,
    width=int(desc_width),
)
desc_text.draw()
    """)
    print("=" * 70)

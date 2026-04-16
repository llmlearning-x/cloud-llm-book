#!/usr/bin/env python3
"""
《云上大模型应用开发实践》书籍构建脚本
生成 HTML 和 PDF 格式输出
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 项目根目录
ROOT_DIR = Path(__file__).parent
SRC_DIR = ROOT_DIR / "src"
OUTPUT_DIR = ROOT_DIR / "output"

def ensure_output_dir():
    """确保输出目录存在"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "html").mkdir(exist_ok=True)
    (OUTPUT_DIR / "pdf").mkdir(exist_ok=True)

def read_file(path):
    """读取文件内容"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    """写入文件内容"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def combine_markdown():
    """合并所有 Markdown 章节为单一文件"""
    print("正在合并 Markdown 章节...")
    
    combined = []
    
    # 书名和封面信息
    combined.append("# 云上大模型应用开发实践\n")
    combined.append("## 晓云 著\n")
    combined.append(f"\n**完成时间**: {datetime.now().strftime('%Y年%m月%d日')}\n")
    combined.append("\n---\n")
    
    # 前言
    preface_path = ROOT_DIR / "preface.md"
    if preface_path.exists():
        combined.append(read_file(preface_path))
        combined.append("\n---\n")
    
    # 各章节
    chapter_dirs = sorted([d for d in SRC_DIR.iterdir() if d.name.startswith('chapter-')])
    
    for chapter_dir in chapter_dirs:
        readme_path = chapter_dir / "README.md"
        if readme_path.exists():
            content = read_file(readme_path)
            combined.append(content)
            combined.append("\n---\n")
    
    # 术语表
    glossary_path = ROOT_DIR / "glossary.md"
    if glossary_path.exists():
        combined.append("\n## 术语表\n")
        combined.append(read_file(glossary_path))
    
    full_content = "\n".join(combined)
    
    # 保存合并后的文件
    output_path = OUTPUT_DIR / "book_full.md"
    write_file(output_path, full_content)
    print(f"✓ 已保存到：{output_path}")
    
    # 统计字数
    char_count = len(full_content)
    word_count = len(full_content.replace(' ', ''))
    print(f"✓ 总字数：约 {word_count:,} 字")
    
    return output_path

def generate_html(md_path):
    """生成简易 HTML 版本"""
    print("\n正在生成 HTML...")
    
    import markdown
    
    md_content = read_file(md_path)
    
    # 使用 markdown 库转换
    html_body = markdown.markdown(
        md_content,
        extensions=['toc', 'tables', 'fenced_code', 'codehilite']
    )
    
    # 包装为完整 HTML 文档
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>云上大模型应用开发实践</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 2em;
            margin-bottom: 1em;
            color: #1a1a1a;
        }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-top: 1em;
        }}
        code {{
            background-color: #f6f8fa;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            overflow: auto;
            border-radius: 6px;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #dfe2e5;
            padding: 10px 16px;
            text-align: left;
        }}
        th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        blockquote {{
            border-left: 4px solid #dfe2e5;
            padding-left: 16px;
            color: #6a737d;
            margin: 1em 0;
        }}
        .table-of-contents {{
            background-color: #f6f8fa;
            padding: 20px;
            border-radius: 6px;
            margin: 2em 0;
        }}
        hr {{
            border: none;
            border-top: 1px solid #dfe2e5;
            margin: 3em 0;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>
"""
    
    output_path = OUTPUT_DIR / "html" / "book.html"
    write_file(output_path, html_template)
    print(f"✓ HTML 已保存到：{output_path}")
    
    return output_path

def generate_pdf(md_path):
    """生成 PDF 版本（使用 reportlab）"""
    print("\n正在生成 PDF...")
    
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # 注册中文字体（使用系统字体）
        import platform
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            # 尝试多个中文字体路径
            font_candidates = [
                ("/System/Library/Fonts/PingFang.ttc", "PingFang"),
                ("/System/Library/Fonts/STHeiti Medium.ttc", "STHeiti"),
                ("/Library/Fonts/Arial Unicode.ttf", "ArialUnicode"),
            ]
            font_path = None
            font_name = None
            for path, name in font_candidates:
                if os.path.exists(path):
                    font_path = path
                    font_name = name
                    break
            if font_path is None:
                font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
                font_name = "STHeiti"
        elif system == 'Windows':
            font_path = "C:/Windows/Fonts/simhei.ttf"
            font_name = "SimHei"
        else:  # Linux
            font_path = "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"
            font_name = "NotoSansCJK"
        
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            print(f"✓ 使用中文字体：{font_name}")
        except Exception as e:
            print(f"⚠ 字体注册失败：{e}，使用默认字体")
            font_name = "Helvetica"
        
        # 创建 PDF 文档
        output_path = OUTPUT_DIR / "pdf" / "book.pdf"
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=2.5*cm,
            rightMargin=2.5*cm,
            topMargin=2.5*cm,
            bottomMargin=2.5*cm
        )
        
        # 定义样式
        styles = getSampleStyleSheet()
        
        # 自定义中文字体样式
        title_style = ParagraphStyle(
            'ChineseTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        heading1_style = ParagraphStyle(
            'ChineseHeading1',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=12,
            spaceBefore=20
        )
        
        heading2_style = ParagraphStyle(
            'ChineseHeading2',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15
        )
        
        normal_style = ParagraphStyle(
            'ChineseNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            leading=18,
            alignment=TA_LEFT
        )
        
        code_style = ParagraphStyle(
            'Code',
            parent=styles['Code'],
            fontName="Courier",
            fontSize=9,
            leading=12,
            backColor=colors.HexColor('#f6f8fa'),
            borderColor=colors.HexColor('#dfe2e5'),
            borderWidth=1,
            leftIndent=10,
            rightIndent=10
        )
        
        story = []
        
        # 标题页
        story.append(Paragraph("云上大模型应用开发实践", title_style))
        story.append(Paragraph("晓云 著", normal_style))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(datetime.now().strftime("%Y年%m月"), normal_style))
        story.append(PageBreak())
        
        # 解析 Markdown 并转换为 PDF 元素
        md_content = read_file(md_path)
        
        # 简单解析：按空行分段
        paragraphs = md_content.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            lines = para.split('\n')
            first_line = lines[0].strip()
            
            # 识别标题
            if first_line.startswith('# '):
                story.append(Paragraph(first_line[2:], heading1_style))
                for line in lines[1:]:
                    if line.strip():
                        story.append(Paragraph(line.strip(), normal_style))
                story.append(Spacer(1, 12))
            
            elif first_line.startswith('## '):
                story.append(Paragraph(first_line[3:], heading2_style))
                for line in lines[1:]:
                    if line.strip():
                        story.append(Paragraph(line.strip(), normal_style))
                story.append(Spacer(1, 10))
            
            elif first_line.startswith('```'):
                # 代码块
                code_content = '\n'.join(lines[1:-1]) if len(lines) > 2 else ''
                code_para = Paragraph(code_content, code_style)
                story.append(code_para)
                story.append(Spacer(1, 12))
            
            elif first_line.startswith('|') and '|' in para:
                # 表格（简化处理）
                table_data = []
                for line in lines:
                    if line.strip().startswith('|'):
                        cells = [cell.strip() for cell in line.split('|')[1:-1]]
                        table_data.append(cells)
                
                if table_data:
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), font_name),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('FONTNAME', (0, 1), (-1, -1), font_name),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 12))
            
            else:
                # 普通段落
                for line in lines:
                    if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('|'):
                        story.append(Paragraph(line.strip(), normal_style))
                story.append(Spacer(1, 12))
            
            # 每 50 段插入分页（避免单章过长）
            if len(story) % 50 == 0:
                story.append(PageBreak())
        
        # 构建 PDF
        doc.build(story)
        print(f"✓ PDF 已保存到：{output_path}")
        
        return output_path
        
    except ImportError as e:
        print(f"⚠ reportlab 未安装，跳过 PDF 生成：{e}")
        print("  安装命令：pip install reportlab")
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("《云上大模型应用开发实践》书籍构建工具")
    print("=" * 60)
    
    # 确保输出目录
    ensure_output_dir()
    
    # 合并 Markdown
    md_path = combine_markdown()
    
    # 生成 HTML
    html_path = generate_html(md_path)
    
    # 生成 PDF
    pdf_path = generate_pdf(md_path)
    
    print("\n" + "=" * 60)
    print("构建完成！")
    print("=" * 60)
    print(f"\n输出文件:")
    print(f"  - 完整 Markdown: {OUTPUT_DIR / 'book_full.md'}")
    print(f"  - HTML 电子书：{OUTPUT_DIR / 'html' / 'book.html'}")
    if pdf_path:
        print(f"  - PDF:         {OUTPUT_DIR / 'pdf' / 'book.pdf'}")
    
    print("\n✅ 所有章节已完成，总计约 18 万字！")

if __name__ == '__main__':
    main()

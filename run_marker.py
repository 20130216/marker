#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import traceback

# 🌍 确保加载环境变量
from marker.settings import load_environment_variables, Settings
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter

def load_and_validate_config() -> Settings:
    """加载并验证配置"""
    # 1. 加载环境变量
    load_environment_variables()
    try:
        settings = Settings()
        print(f"✅ 配置验证通过: OPENAI_MODEL={settings.OPENAI_MODEL}")
        return settings
    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        print("请检查 .env 文件内容示例:")
        print("OPENAI_MODEL=gemini-2.5-pro-exp-03-25")
        print("OPENAI_API_KEY=sk-xxx")
        raise    

    # 2. 创建 Settings 实例
    settings = Settings()
    settings.OUTPUT_DIR = os.path.normpath(settings.OUTPUT_DIR)  # 路径标准化

    # 3. 结构化调试输出
    print("\n" + "="*50)
    print("🔧 运行前配置验证")
    print(f"| {'配置项':<20} | {'值':<40} |")
    print("|----------------------|----------------------------------------|")
    print(f"| LLM_SERVICE         | {settings.LLM_SERVICE!r:<40} |")
    print(f"| OPENAI_MODEL        | {settings.OPENAI_MODEL!r:<40} |")
    print(f"| OPENAI_BASE_URL     | {settings.OPENAI_BASE_URL!r:<40} |")
    print(f"| OPENAI_API_KEY      | {'***'+settings.OPENAI_API_KEY[-3:] if settings.OPENAI_API_KEY else '未设置':<40} |")
    print(f"| OUTPUT_DIR          | {settings.OUTPUT_DIR!r:<40} |")
    print("="*50 + "\n")

    # 4. 关键配置验证
    if not settings.OPENAI_API_KEY:
        raise ValueError("❌ 缺少 OPENAI_API_KEY，请在 local.env 中配置")
    if not settings.OPENAI_MODEL:
        raise ValueError("❌ 缺少 OPENAI_MODEL，请在 local.env 中配置")
    if not settings.OPENAI_BASE_URL:
        raise ValueError("❌ 缺少 OPENAI_BASE_URL，请在 local.env 中配置")

    return settings

def process_pdf(input_path: str, output_dir: str = None) -> str:
    """主处理流程：解析PDF为Markdown"""
    # 读取 local.env 和其他配置。
    settings = load_and_validate_config()

    # 添加调试输出（验证LLM配置）
    print("===以下是 run_marker.py中的系列参数 ===")
    print(f"🔍 环境变量验证:")
    print(f"  [Settings类] 模型: {settings.OPENAI_MODEL}")
    print(f"  [os.environ] 模型: {os.getenv('OPENAI_MODEL')}")
    print(f"  [Settings类] API密钥: {'***'+settings.OPENAI_API_KEY[-3:] if settings.OPENAI_API_KEY else '未设置'}")
    print(f"  [os.environ] API密钥: {'***'+os.getenv('OPENAI_API_KEY')[-3:] if os.getenv('OPENAI_API_KEY') else '未设置'}")
    print(f"  API端点: {settings.OPENAI_BASE_URL}")
    print(f"  服务类型: {settings.LLM_SERVICE}")
    print(f"  DEBUG: {settings.DEBUG}")
    print(f"  DEBUG_LEVEL {settings.DEBUG_LEVEL}")
    print("\--- 新增参数验证 ---")
    print(f"  FORCE_OCR: {settings.FORCE_OCR}")
    print(f"  PAGE_RANGE: {settings.PAGE_RANGE}")
    print(f"  LANGUAGES: {settings.LANGUAGES}")
    print(f"  MAX_RETRIES: {settings.MAX_RETRIES}") 
    
    # 构造ConfigParser配置
    config = {
        'use_llm': True,
        'llm_service': settings.LLM_SERVICE,
        'openai_api_key': settings.OPENAI_API_KEY,
        'openai_model': settings.OPENAI_MODEL,
        'openai_base_url': settings.OPENAI_BASE_URL,
        'output_dir': output_dir or settings.OUTPUT_DIR,
        'output_format': settings.OUTPUT_FORMAT,
        'force_ocr': settings.FORCE_OCR,  # 从这里新增几个参数
        'page_range': settings.PAGE_RANGE,
        'languages': settings.LANGUAGES,
        'max_retries': settings.MAX_RETRIES,
    }
    
    # 添加debug信息
    print(f"✅ 最终LLM配置: service={config['llm_service']}, model={config['openai_model']}")  # 添加此行
    print("===以上是 run_marker.py中的系列参数 ===\n")
    config_parser = ConfigParser(config)

    # 构造 PDF 转换器 ,将 PDF 转为中间结构（如图片、文本块等）。
    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
        llm_service=config_parser.get_llm_service()
    )

    # 解析 PDF
    result = converter(input_path)

    # 构造输出路径
    output_path = str(Path(config['output_dir']) / f"{Path(input_path).stem}.md")

    # 安全地写入文件
    content = result.to_markdown() if hasattr(result, "to_markdown") else str(result)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='📄 PDF 转 Markdown 工具')
    parser.add_argument('input_file', help='输入的PDF文件路径')
    parser.add_argument('-o', '--output-dir', help='覆盖默认输出目录')
    args = parser.parse_args()

    try:
        output_path = process_pdf(args.input_file, args.output_dir)
        print(f"\n✅ 转换完成！结果保存在: {output_path}")
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        if os.getenv('DEBUG', '').lower() in ('true', '1', 't'):
            traceback.print_exc()
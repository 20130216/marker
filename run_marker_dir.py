import os
import sys
from datetime import datetime
from run_marker import process_pdf

def process_all_pdfs(input_dir, output_root=None):
    # 1. 生成平行输出根目录
    input_dir = os.path.abspath(input_dir)
    parent_dir = os.path.dirname(input_dir)
    base_name = os.path.basename(input_dir)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_root is None:
        output_root = os.path.join(parent_dir, f"{base_name}--解析文件{now_str}")
    if not os.path.exists(output_root):
        os.makedirs(output_root)
    print(f"输出根目录: {output_root}")

    # 2. 遍历所有PDF，保持目录结构
    pdf_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(input_dir)
        for file in files if file.lower().endswith('.pdf')
    ]
    print(f"共发现 {len(pdf_files)} 个PDF文件。")
    for pdf in pdf_files:
        try:
            # 计算相对路径
            rel_path = os.path.relpath(os.path.dirname(pdf), input_dir)
            target_output_dir = os.path.join(output_root, rel_path)
            os.makedirs(target_output_dir, exist_ok=True)
            print(f"正在处理: {pdf}")
            out_path = process_pdf(pdf, target_output_dir)
            print(f"✅ 完成: {out_path}")
        except Exception as e:
            print(f"❌ 处理失败: {pdf}，原因: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python run_marker_dir.py <输入文件夹> [输出根文件夹]")
        sys.exit(1)
    input_dir = sys.argv[1]
    output_root = sys.argv[2] if len(sys.argv) > 2 else None
    process_all_pdfs(input_dir, output_root)
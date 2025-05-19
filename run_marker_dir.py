# run_marker_dir.py
import os
import sys
from run_marker import process_pdf

def process_all_pdfs(input_dir, output_dir=None):
    pdf_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(input_dir)
        for file in files if file.lower().endswith('.pdf')
    ]
    print(f"共发现 {len(pdf_files)} 个PDF文件。")
    for pdf in pdf_files:
        try:
            print(f"正在处理: {pdf}")
            out_path = process_pdf(pdf, output_dir)
            print(f"✅ 完成: {out_path}")
        except Exception as e:
            print(f"❌ 处理失败: {pdf}，原因: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python run_marker_dir.py <输入文件夹> [输出文件夹]")
        sys.exit(1)
    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    process_all_pdfs(input_dir, output_dir)
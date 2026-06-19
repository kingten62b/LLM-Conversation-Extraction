#!/usr/bin/env python3
"""
客服对话结构化提取 - 主入口

使用方法:
    conda activate 0108
    python run_extraction.py
    python run_extraction.py --skip-validate  # 跳过验证
    python run_extraction.py --validate-only  # 仅验证已有结果
"""

import json
import sys
import os


def main():
    skip_validate = "--skip-validate" in sys.argv
    validate_only = "--validate-only" in sys.argv

    # 加载对话数据
    with open("task2_conversations.json", "r", encoding="utf-8") as f:
        conversations = json.load(f)
    print(f"加载 {len(conversations)} 条对话\n")

    if not validate_only:
        from extraction.extractor import run_extraction
        results = run_extraction(conversations)

        os.makedirs("output", exist_ok=True)
        with open("output/extraction_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到 output/extraction_results.json")
    else:
        with open("output/extraction_results.json", "r", encoding="utf-8") as f:
            results = json.load(f)
        print(f"加载已有结果：{len(results)} 条")

    if not skip_validate:
        print("\n" + "=" * 60)
        print("开始准确性验证")
        print("=" * 60)
        from extraction.validator import validate_results
        validate_results(results)


if __name__ == "__main__":
    main()

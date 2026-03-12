#!/usr/bin/env python3
"""
完整工作流：从item.md提取物品，生成25宫格图片，切图并去背景
"""

import argparse
import json
import os
import re
from pathlib import Path

# 物品名称列表
ITEM_NAMES = [
    # 第1行
    "gold_coin", "fossil_1", "fossil_2", "fossil_3", "fossil_4",
    # 第2行
    "fossil_5", "fossil_6", "fossil_7", "fossil_8", "fossil_full",
    # 第3行
    "dragon_egg_fragment_1", "dragon_egg_fragment_2", "dragon_egg_1", "dragon_egg_2", "tool_1",
    # 第4行
    "tool_2", "tool_3", "tool_4", "tool_5", "tool_6",
    # 第5行
    "tool_7", "tool_8", "tool_9", "device_1", "device_2",
]


def extract_items_from_md(md_file: str, max_items: int = 25) -> list:
    """从item.md提取物品列表"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    items = []
    # 匹配 ## 分类标题 和 - 物品名
    current_category = ""
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith('## '):
            current_category = line[3:].strip()
        elif line.startswith('- '):
            item_name = line[2:].strip()
            items.append({
                'name': item_name.replace(' ', '_'),
                'category': current_category
            })
            if len(items) >= max_items:
                break

    return items[:max_items]


def create_grid_prompt(items: list) -> str:
    """创建25宫格的提示词"""
    # 将物品分成5行5列
    rows = []
    for row_idx in range(5):
        row_items = items[row_idx * 5:(row_idx + 1) * 5]
        row_str = ", ".join(row_items)
        rows.append(row_str)

    prompt = f"""A 5x5 grid of cartoon game item icons, flat design style, vibrant colors, WHITE BACKGROUND. Each cell has clear black border. Grid layout:

Row 1: {rows[0]}
Row 2: {rows[1]}
Row 3: {rows[2]}
Row 4: {rows[3]}
Row 5: {rows[4]}

Each item in its own square cell, pixel art aesthetic, clean and simple."""
    return prompt


def main():
    parser = argparse.ArgumentParser(description="完整工作流：生成25宫格图片并切图")
    parser.add_argument("--items", default="item.md", help="物品列表文件")
    parser.add_argument("--count", type=int, default=25, help="生成的物品数量")
    parser.add_argument("--output-dir", "-o", default="./output", help="输出目录")
    parser.add_argument("--api-key", "-k", default="s8d1MThUUKpYWO9kO6Br", help="CloudsWay API密钥")
    parser.add_argument("--skip-generate", action="store_true", help="跳过图片生成")
    parser.add_argument("--skip-cut", action="store_true", help="跳过切图")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 提取物品列表
    print("=" * 50)
    print("步骤1: 提取物品列表")
    print("=" * 50)
    items = extract_items_from_md(args.items, args.count)
    print(f"提取了 {len(items)} 个物品:")
    for i, item in enumerate(items):
        print(f"  {i+1}. {item['name']} ({item['category']})")

    # 2. 生成25宫格图片
    print("\n" + "=" * 50)
    print("步骤2: 生成25宫格图片")
    print("=" * 50)

    grid_image_path = output_dir / "grid_25.png"

    if args.skip_generate:
        print("跳过图片生成")
    else:
        # 创建提示词
        prompt = create_grid_prompt([item['name'] for item in items])
        print(f"提示词: {prompt[:200]}...")

        # 调用API生成（这里需要调用generate_images.py的逻辑）
        from generate_images import generate_image_cloudsway
        from dataclasses import dataclass

        @dataclass
        class PromptItem:
            name: str
            prompt: str

        item = PromptItem(name="grid_25", prompt=prompt)
        generate_image_cloudsway(item.prompt, args.api_key, grid_image_path)

    # 3. 切图并去背景
    print("\n" + "=" * 50)
    print("步骤3: 切图并去背景")
    print("=" * 50)

    if args.skip_cut:
        print("跳过切图")
    else:
        from cut_grid import remove_background
        from PIL import Image

        img = Image.open(grid_image_path)
        w, h = img.size
        cell_w, cell_h = w // 5, h // 5

        cut_dir = output_dir / "cut_25"
        cut_dir.mkdir(parents=True, exist_ok=True)

        # 扩展物品列表到25个
        item_names = ITEM_NAMES[:25]

        for row in range(5):
            for col in range(5):
                # 计算格子位置（考虑格子线）
                margin = 2  # 格子线宽度
                left = col * cell_w + margin
                top = row * cell_h + margin
                right = (col + 1) * cell_w - margin
                bottom = (row + 1) * cell_h - margin

                cell = img.crop((left, top, right, bottom))

                name = item_names[row * 5 + col] if row * 5 + col < len(item_names) else f"item_{row*5+col}"

                # 保存临时文件
                temp_path = cut_dir / f"{name}_temp.png"
                cell.save(temp_path)

                # 去背景
                final_path = cut_dir / f"{name}.png"
                remove_background(str(temp_path), str(final_path))

                # 删除临时文件
                if temp_path.exists():
                    temp_path.unlink()

                print(f"  Saved: {name}.png")

        print(f"\n切图完成! 输出目录: {cut_dir}")
        print(f"共生成 {len(list(cut_dir.glob('*.png')))} 个文件")

    print("\n" + "=" * 50)
    print("工作流完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""25宫格切图工具 - 切图+去背景+自动居中"""

import argparse
import os
from pathlib import Path
from PIL import Image
import numpy as np


# 25个物品名称
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


def get_background_color(arr):
    """获取背景色（四个角落的平均值）"""
    h, w = arr.shape[:2]
    corners = [arr[0, 0, :3], arr[0, w-1, :3], arr[h-1, 0, :3], arr[h-1, w-1, :3]]
    return np.mean(corners, axis=0).astype(int)


def find_item_bounds(cell_arr, bg_color, threshold=40):
    """
    找到物品的边界框
    返回: (min_x, min_y, max_x, max_y)
    """
    h, w = cell_arr.shape[:2]

    # 计算每个像素与背景色的距离
    pixels = cell_arr[:, :, :3]
    distances = np.sqrt(np.sum((pixels - bg_color) ** 2, axis=2))

    # 找到所有非背景像素
    mask = distances > threshold

    if not np.any(mask):
        # 没有找到物品，返回整个区域
        return 0, 0, w, h

    # 找到边界
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    min_y = np.argmax(rows)
    max_y = h - np.argmax(rows[::-1]) - 1
    min_x = np.argmax(cols)
    max_x = w - np.argmax(cols[::-1]) - 1

    return min_x, min_y, max_x, max_y


def crop_and_center(cell_img, target_size=None):
    """
    裁剪并居中物品
    1. 找到物品边界
    2. 以边界中心为基准裁剪成正方形
    """
    # 转换为 numpy 数组
    if cell_img.mode != 'RGBA':
        cell_img = cell_img.convert('RGBA')
    arr = np.array(cell_img)

    # 获取背景色
    bg_color = get_background_color(arr)

    # 找到物品边界
    min_x, min_y, max_x, max_y = find_item_bounds(arr, bg_color)

    # 边界框的宽高
    item_w = max_x - min_x
    item_h = max_y - min_y

    # 取最大边作为正方形边长
    square_size = max(item_w, item_h)

    # 边界框中心
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2

    # 计算裁剪区域（以中心为基准）
    half = square_size // 2
    left = center_x - half
    top = center_y - half
    right = left + square_size
    bottom = top + square_size

    # 边界检查
    h, w = arr.shape[:2]
    if left < 0:
        left = 0
        right = square_size
    if top < 0:
        top = 0
        right = square_size
    if right > w:
        right = w
        left = right - square_size
    if bottom > h:
        bottom = h
        top = bottom - square_size

    # 裁剪
    cropped = cell_img.crop((left, top, right, bottom))

    # 调整为目标尺寸
    if target_size:
        cropped = cropped.resize((target_size, target_size), Image.LANCZOS)

    return cropped


def remove_background(input_path: str, output_path: str, threshold: int = 35) -> None:
    """移除图片背景（漫水填充算法）"""
    from collections import deque

    img = Image.open(input_path).convert('RGBA')
    arr = np.array(img)
    h, w = arr.shape[:2]

    # 获取背景色
    bg_color = get_background_color(arr)

    # 漫水填充
    visited = np.zeros((h, w), dtype=bool)

    def is_background(r, g, b):
        dist = np.sqrt((r - bg_color[0])**2 + (g - bg_color[1])**2 + (b - bg_color[2])**2)
        return dist < threshold

    queue = deque()

    # 初始化边缘像素
    for x in range(w):
        for y in [0, h-1]:
            if not visited[y, x]:
                r, g, b = arr[y, x, :3]
                if is_background(r, g, b):
                    queue.append((y, x))
                    visited[y, x] = True

    for y in range(h):
        for x in [0, w-1]:
            if not visited[y, x]:
                r, g, b = arr[y, x, :3]
                if is_background(r, g, b):
                    queue.append((y, x))
                    visited[y, x] = True

    # BFS
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    while queue:
        y, x = queue.popleft()
        for dy, dx in directions:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                r, g, b = arr[ny, nx, :3]
                if is_background(r, g, b):
                    visited[ny, nx] = True
                    queue.append((ny, nx))

    # 背景设为透明
    arr[visited, 3] = 0

    result = Image.fromarray(arr, 'RGBA')
    result.save(output_path)


def crop_grid_25(image_path: str, output_dir: str, remove_bg: bool = True,
                 margin: int = 3, center_size: int = None):
    """将25宫格图片切成25个小图，自动居中"""
    img = Image.open(image_path)
    w, h = img.size
    cell_w, cell_h = w // 5, h // 5

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"图片尺寸: {w}x{h}")
    print(f"格子尺寸: {cell_w}x{cell_h}")
    print(f"边距: {margin}px")
    print(f"居中裁剪: {center_size}x{center_size if center_size else 'auto'}")

    for row in range(5):
        for col in range(5):
            # 计算格子位置
            left = col * cell_w + margin
            top = row * cell_h + margin
            right = (col + 1) * cell_w - margin
            bottom = (row + 1) * cell_h - margin

            cell = img.crop((left, top, right, bottom))

            name = ITEM_NAMES[row * 5 + col] if row * 5 + col < len(ITEM_NAMES) else f"item_{row*5+col}"

            # 临时保存
            temp_path = out / f"{name}_temp.png"
            cell.save(temp_path)

            # 去除背景
            if remove_bg:
                # 先去背景
                bg_removed_path = out / f"{name}_nobg.png"
                remove_background(str(temp_path), str(bg_removed_path), threshold=35)

                # 再居中裁剪
                if center_size:
                    final_img = Image.open(str(bg_removed_path))
                    final_img = crop_and_center(final_img, target_size=center_size)
                    final_path = out / f"{name}.png"
                    final_img.save(final_path)
                    bg_removed_path.unlink()
                else:
                    final_path = out / f"{name}.png"
                    bg_removed_path.rename(final_path)

                temp_path.unlink()
            else:
                # 不去背景，直接居中裁剪
                if center_size:
                    final_img = crop_and_center(cell, target_size=center_size)
                    final_path = out / f"{name}.png"
                    final_img.save(final_path)
                else:
                    final_path = out / f"{name}.png"
                    cell.save(final_path)
                temp_path.unlink()

            print(f"  Saved: {name}.png")

    print(f"\n完成! 共生成 {len(list(out.glob('*.png')))} 个文件")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="25宫格切图工具 - 支持居中裁剪")
    parser.add_argument("input", help="输入的25宫格图片路径")
    parser.add_argument("-o", "--output", default="./output/cut_centered", help="输出目录")
    parser.add_argument("--no-bg-remove", action="store_true", help="不移除背景")
    parser.add_argument("--margin", type=int, default=3, help="格子边距")
    parser.add_argument("--size", type=int, default=None, help="居中裁剪的目标尺寸")

    args = parser.parse_args()

    print("25宫格切图工具 (居中版)")
    print(f"  输入: {args.input}")
    print(f"  输出: {args.output}")
    print(f"  移除背景: {not args.no_bg_remove}")
    print(f"  边距: {args.margin}")

    crop_grid_25(args.input, args.output, not args.no_bg_remove, args.margin, args.size)

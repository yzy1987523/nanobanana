#!/usr/bin/env python3
"""改进版去背景 - 使用漫水填充算法，保留物品内部像素"""

import argparse
import os
from pathlib import Path
from PIL import Image
import numpy as np
from collections import deque


def flood_fill_background(img: Image.Image, threshold: int = 35) -> Image.Image:
    """
    使用漫水填充算法去除背景
    思路：从图片边缘开始 flood fill，标记所有背景像素
    剩余未标记的像素就是物体
    """
    # 确保是 RGBA 模式
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    arr = np.array(img)
    h, w = arr.shape[:2]

    # 如果没有 alpha 通道，添加一个
    if arr.shape[2] == 3:
        arr = np.concatenate([arr, np.full((h, w, 1), 255, dtype=np.uint8)], axis=2)

    # 获取背景色（四个角落的平均值）
    corners = [arr[0, 0, :3], arr[0, w-1, :3], arr[h-1, 0, :3], arr[h-1, w-1, :3]]
    bg_color = np.mean(corners, axis=0).astype(int)

    # 创建访问标记数组
    visited = np.zeros((h, w), dtype=bool)

    # 判断像素是否接近背景色
    def is_background(r, g, b):
        dist = np.sqrt((r - bg_color[0])**2 + (g - bg_color[1])**2 + (b - bg_color[2])**2)
        return dist < threshold

    # 从边缘开始漫水填充
    queue = deque()

    # 将所有边缘像素加入队列
    for x in range(w):
        if not visited[0, x]:
            r, g, b = arr[0, x, :3]
            if is_background(r, g, b):
                queue.append((0, x))
                visited[0, x] = True

        if not visited[h-1, x]:
            r, g, b = arr[h-1, x, :3]
            if is_background(r, g, b):
                queue.append((h-1, x))
                visited[h-1, x] = True

    for y in range(h):
        if not visited[y, 0]:
            r, g, b = arr[y, 0, :3]
            if is_background(r, g, b):
                queue.append((y, 0))
                visited[y, 0] = True

        if not visited[y, w-1]:
            r, g, b = arr[y, w-1, :3]
            if is_background(r, g, b):
                queue.append((y, w-1))
                visited[y, w-1] = True

    # BFS 漫水填充
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

    # 将未访问的像素设为透明（即背景像素）
    # 反转：visited=True 表示背景，visited=False 表示物体
    background_mask = visited
    arr[background_mask, 3] = 0

    return Image.fromarray(arr, 'RGBA')


def remove_background_v2(input_path: str, output_path: str, threshold: int = 35) -> None:
    """改进版去背景"""
    img = Image.open(input_path)
    result = flood_fill_background(img, threshold)
    result.save(output_path)


def process_folder(input_dir: str, output_dir: str, threshold: int = 35):
    """处理文件夹"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for img_file in sorted(input_path.glob("*.png")):
        print(f"处理: {img_file.name}")
        remove_background_v2(str(img_file), str(output_path / img_file.name), threshold)
        print(f"  已保存: {img_file.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="改进版去背景 - 使用漫水填充")
    parser.add_argument("input", help="输入文件夹或文件")
    parser.add_argument("-o", "--output", default=None, help="输出文件夹")
    parser.add_argument("-t", "--threshold", type=int, default=35, help="背景色相似度阈值")

    args = parser.parse_args()

    input_path = Path(args.input)

    if input_path.is_file():
        # 单文件处理
        output_path = args.output or str(input_path.parent / f"{input_path.stem}_nobg.png")
        print(f"处理: {input_path.name}")
        remove_background_v2(str(input_path), output_path, args.threshold)
        print(f"已保存: {output_path}")
    else:
        # 文件夹处理
        output_dir = args.output or str(input_path.parent / "nobg_v2")
        print(f"输入: {input_path}")
        print(f"输出: {output_dir}")
        process_folder(str(input_path), output_dir, args.threshold)
        print("完成!")

#!/usr/bin/env python3
"""
批量图片生成工具
根据提示词列表使用魔塔 API 依次生成图片并保存到本地
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import requests


# 默认配置
DEFAULT_API_KEY = "ms-28230386-a9ef-41bd-8982-a2d474026996"
DEFAULT_MODEL = "Qwen/Qwen-Image"
BASE_URL = "https://api-inference.modelscope.cn/v1"

# 轮询配置
MAX_POLL_ATTEMPTS = 60
POLL_INTERVAL = 5  # 秒
MAX_DOWNLOAD_RETRIES = 3
MAX_API_RETRIES = 3


@dataclass
class PromptItem:
    """提示词项"""
    name: str
    prompt: str


def submit_task(prompt: str, model: str, api_key: str) -> str:
    """
    提交图片生成任务（带重试机制）
    
    Args:
        prompt: 图片描述提示词
        model: 模型名称
        api_key: API 密钥
    
    Returns:
        任务 ID
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-ModelScope-Async-Mode": "true"
    }
    
    payload = {
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1
    }
    
    for attempt in range(MAX_API_RETRIES):
        try:
            response = requests.post(
                f"{BASE_URL}/images/generations",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"提交任务失败: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # 检查是否直接返回结果（同步模式）
            if "data" in data and len(data["data"]) > 0:
                return data["data"][0].get("url", "")
            
            # 异步模式返回 task_id
            task_id = data.get("task_id")
            if not task_id:
                raise Exception(f"响应中缺少 task_id: {data}")
            
            return task_id
        except Exception as e:
            if attempt < MAX_API_RETRIES - 1:
                print(f"  API请求失败，3秒后重试... ({attempt + 1}/{MAX_API_RETRIES})")
                time.sleep(3)
            else:
                raise


def poll_task_status(task_id: str, api_key: str) -> dict:
    """
    轮询任务状态（带重试机制）
    
    Args:
        task_id: 任务 ID
        api_key: API 密钥
    
    Returns:
        任务结果数据
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-ModelScope-Task-Type": "image_generation"
    }
    
    for attempt in range(MAX_POLL_ATTEMPTS):
        try:
            response = requests.get(
                f"{BASE_URL}/tasks/{task_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"查询任务失败: {response.status_code} - {response.text}")
            
            data = response.json()
            status = data.get("task_status")
            
            print(f"  轮询 #{attempt + 1}: 状态={status}")
            
            if status == "SUCCEED":
                return data
            elif status == "FAILED":
                raise Exception(f"任务失败: {data}")
            
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            if attempt < MAX_POLL_ATTEMPTS - 1:
                print(f"  查询失败，3秒后重试...")
                time.sleep(3)
            else:
                raise
    
    raise Exception(f"任务超时: 超过 {MAX_POLL_ATTEMPTS * POLL_INTERVAL} 秒")


def download_image(url: str, save_path: Path) -> None:
    """
    下载图片并保存（带重试机制）
    
    Args:
        url: 图片 URL
        save_path: 保存路径
    """
    for attempt in range(MAX_DOWNLOAD_RETRIES):
        try:
            response = requests.get(url, stream=True, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"下载图片失败: {response.status_code}")
            
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return
        except Exception as e:
            if attempt < MAX_DOWNLOAD_RETRIES - 1:
                print(f"  下载失败，{3}秒后重试... ({attempt + 1}/{MAX_DOWNLOAD_RETRIES})")
                time.sleep(3)
            else:
                raise Exception(f"下载图片失败 (已重试{MAX_DOWNLOAD_RETRIES}次): {e}")


def load_prompts(prompts_file: str) -> list[PromptItem]:
    """
    加载提示词列表
    
    Args:
        prompts_file: 提示词 JSON 文件路径
    
    Returns:
        提示词项列表
    """
    with open(prompts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return [PromptItem(name=item["name"], prompt=item["prompt"]) for item in data]


def generate_image(item: PromptItem, output_dir: Path, model: str, api_key: str) -> str:
    """
    生成单张图片
    
    Args:
        item: 提示词项
        output_dir: 输出目录
        model: 模型名称
        api_key: API 密钥
    
    Returns:
        保存的文件路径
    """
    print(f"\n[{item.name}] 开始生成...")
    print(f"  提示词: {item.prompt}")
    
    # 提交任务
    task_id_or_url = submit_task(item.prompt, model, api_key)
    
    # 判断是 URL 还是 task_id
    if task_id_or_url.startswith("http"):
        # 同步模式，直接获取到 URL
        image_url = task_id_or_url
        print(f"  同步模式，图片已生成")
    else:
        # 异步模式，需要轮询
        print(f"  任务 ID: {task_id_or_url}")
        result = poll_task_status(task_id_or_url, api_key)
        
        # 提取图片 URL
        image_url = result.get("output_images", [None])[0]
        if not image_url:
            raise Exception(f"无法获取图片 URL: {result}")
    
    print(f"  图片 URL: {image_url}")
    
    # 下载并保存
    save_path = output_dir / f"{item.name}.png"
    download_image(image_url, save_path)
    
    print(f"  已保存: {save_path}")
    return str(save_path)


def main():
    parser = argparse.ArgumentParser(description="批量图片生成工具")
    parser.add_argument(
        "--prompts", "-p",
        default="prompts.json",
        help="提示词 JSON 文件路径 (默认: prompts.json)"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="图片输出目录 (默认: ./output)"
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"模型名称 (默认: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--api-key", "-k",
        default=DEFAULT_API_KEY,
        help="魔塔 API 密钥"
    )
    
    args = parser.parse_args()
    
    # 检查提示词文件
    if not os.path.exists(args.prompts):
        print(f"错误: 提示词文件不存在: {args.prompts}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载提示词
    print(f"加载提示词文件: {args.prompts}")
    prompts = load_prompts(args.prompts)
    print(f"共 {len(prompts)} 个提示词")
    
    # 依次生成图片
    success_count = 0
    failed_items = []
    
    for i, item in enumerate(prompts, 1):
        print(f"\n{'='*50}")
        print(f"进度: {i}/{len(prompts)}")
        
        try:
            generate_image(item, output_dir, args.model, args.api_key)
            success_count += 1
        except Exception as e:
            print(f"  错误: {e}")
            failed_items.append(item.name)
    
    # 汇总结果
    print(f"\n{'='*50}")
    print(f"生成完成!")
    print(f"  成功: {success_count}")
    print(f"  失败: {len(failed_items)}")
    
    if failed_items:
        print(f"  失败项目: {', '.join(failed_items)}")
    
    print(f"\n输出目录: {output_dir.absolute()}")


if __name__ == "__main__":
    main()

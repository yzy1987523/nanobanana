# 批量图片生成工具

使用魔塔（ModelScope）API 批量生成图片的工具。

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
# 使用默认配置
python generate_images.py

# 指定提示词文件和输出目录
python generate_images.py --prompts prompts.json --output ./output

# 指定模型
python generate_images.py --model Qwen/Qwen-Image
```

## 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--prompts` | `-p` | `prompts.json` | 提示词 JSON 文件路径 |
| `--output` | `-o` | `./output` | 图片输出目录 |
| `--model` | `-m` | `Qwen/Qwen-Image` | 使用的模型 |
| `--api-key` | `-k` | (内置) | 魔塔 API 密钥 |

## 提示词格式

```json
[
  {"name": "apple", "prompt": "a red shiny apple on a white background"},
  {"name": "banana", "prompt": "a yellow banana on a wooden table"},
  {"name": "orange", "prompt": "a fresh orange with green leaves"}
]
```

- `name`: 图片文件名（不含扩展名）
- `prompt`: 图片描述提示词

## 输出

生成的图片保存在指定目录，文件名使用 `name` 字段命名：

```
output/
├── apple.png
├── banana.png
└── orange.png
```

# 批量图片生成工具

使用 AI（CloudsWay / ModelScope）API 批量生成游戏物品图片的工具。

## 功能特点

- AI 图片生成（支持 CloudsWay、ModelScope）
- 自动生成 5x5 网格图片（25 宫格）
- 智能切图（网格 → 25 张独立图片）
- 漫水填充去背景（保留物品内部细节）
- 自动居中裁剪

---

## 环境配置

### 1. 安装 Python

下载并安装 Python 3.8+：https://www.python.org/downloads/

**重要**：安装时勾选 `Add Python to PATH`

### 2. 安装依赖

打开终端（命令提示符/PowerShell），运行：

```bash
pip install pillow numpy requests
```

### 3. API 密钥配置

工具使用 CloudsWay API 生成图片，需要配置 API 密钥。

编辑 `generate_images.py`，修改第 19 行的 API 密钥：

```python
DEFAULT_API_KEY = "你的API密钥"
```

获取 API 密钥：访问 https://www.cloudsway.net/ 注册并获取

---

## 快速开始

### 完整工作流（推荐）

一条命令完成：生成图片 → 切图 → 去背景 → 居中

```bash
python workflow.py --count 25 -o output/my_items
```

参数说明：
- `--count 25`：生成 25 个物品（5x5 网格）
- `-o output/my_items`：输出目录

### 分步骤执行

#### 步骤 1：生成网格图片

```bash
python generate_images.py -p prompts_25.json -o output
```

- 输入：prompts_25.json（提示词配置）
- 输出：output/grid_25.png

#### 步骤 2：切图 + 去背景 + 居中

```bash
python cut_grid_25_v2.py output/grid_25.png -o output/items --margin 5 --size 180
```

参数说明：
- `output/grid_25.png`：输入的网格图片
- `-o output/items`：输出目录
- `--margin 5`：边缘留白（去除网格线）
- `--size 180`：输出图片尺寸（180x180 像素）

---

## 使用示例

### 示例 1：生成新的物品图片

1. 编辑 prompts_25.json，修改物品描述
2. 运行：
   ```bash
   python workflow.py --count 25 -o output/new_items
   ```

### 示例 2：只切图（不生成）

已有网格图片，想重新切图：

```bash
python cut_grid_25_v2.py 你的网格图片.png -o output/cut_result --margin 5 --size 180
```

### 示例 3：调整去背景阈值

如果去背景效果不好，可以调整阈值：

```bash
python cut_grid_25_v2.py output/grid_25.png -o output/test --margin 5 --size 180 -t 25
```

- `-t 25`：更保守（保留更多颜色）
- `-t 50`：更激进（去除更多背景）

---

## 文件说明

| 文件 | 用途 |
|------|------|
| generate_images.py | AI 图片生成 |
| cut_grid_25_v2.py | 25 宫格切图 + 去背景 + 居中 |
| workflow.py | 一键完成所有步骤 |
| prompts_25.json | 物品提示词配置 |
| remove_background_floodfill.py | 独立的去背景工具 |

---

## 注意事项

### 1. API 密钥
- 默认的 API 密钥可能已失效，请替换为你自己的
- API 有调用次数限制，请注意使用

### 2. 图片质量
- 生成的图片质量取决于 AI 模型
- 如果有不满意的图片，可以：
  - 修改 prompts_25.json 中的提示词
  - 重新生成

### 3. 网格线问题
- 如果图片有网格线，增加 `--margin` 值（如 8 或 10）
- 示例：`--margin 8`

### 4. 去背景问题
- 如果物品被过度去除，减小阈值 `-t`
- 如果背景没去干净，增大阈值 `-t`

### 5. 输出尺寸
- `--size` 参数决定输出图片大小
- 游戏使用建议：128x128 或 256x256

---

## 故障排除

### Q: 运行报错 "No module named 'PIL'"
A: 未安装依赖，运行 `pip install pillow numpy requests`

### Q: 图片生成失败
A: 检查 API 密钥是否正确，网络是否正常

### Q: 切图位置不对
A: 调整 `--margin` 参数，或检查原图尺寸是否为正方形

### Q: 去背景把物品也删了
A: 减小阈值，如 `-t 20` 或 `-t 15`

---

## 项目结构

```
nanobanana/
├── generate_images.py      # 图片生成
├── cut_grid_25_v2.py       # 切图工具
├── workflow.py             # 一键工作流
├── prompts_25.json         # 提示词配置
├── remove_background_floodfill.py  # 去背景
└── output/                 # 输出目录
    ├── grid_25.png         # 生成的网格图
    └── items/              # 切分后的物品图
        ├── gold_coin.png
        ├── fossil_1.png
        └── ...
```

---

## 常见问题

### 如何修改物品列表？
编辑 `prompts_25.json`，修改 `prompt` 中的物品名称

### 如何只生成不切图？
使用 `generate_images.py` 即可

### 如何只切图不生成？
使用 `cut_grid_25_v2.py`，传入已有的网格图片

---

## 原始参数说明（向下兼容）

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--prompts` | `-p` | `prompts.json` | 提示词 JSON 文件路径 |
| `--output` | `-o` | `./output` | 图片输出目录 |
| `--model` | `-m` | `Qwen/Qwen-Image` | 使用的模型 |
| `--api-key` | `-k` | (内置) | API 密钥 |

### 提示词格式

```json
[
  {"name": "apple", "prompt": "a red shiny apple on a white background"},
  {"name": "banana", "prompt": "a yellow banana on a wooden table"},
  {"name": "orange", "prompt": "a fresh orange with green leaves"}
]
```

- `name`: 图片文件名（不含扩展名）
- `prompt`: 图片描述提示词

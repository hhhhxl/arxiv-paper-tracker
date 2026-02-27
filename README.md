# arXiv智能论文追踪器

基于**胶水编程**原则构建的命令行工具，用于自动化追踪arXiv最新论文。

> 核心原则：能抄不写，能连不造，能复用不原创

---

## 特性

- 🔍 **智能检索** - 支持学科分类和关键词组合查询
- 📊 **多格式输出** - 终端、TXT、Markdown、CSV、JSON
- 🚫 **自动去重** - 基于arXiv ID的历史记录去重
- ⏰ **定时任务** - 支持Crontab无人值守运行
- 🎯 **灵活配置** - 配置文件/命令行/交互式三种模式

---

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本用法

```bash
# 使用默认配置文件
python arxiv_tracker.py --config config.json

# 交互式配置（首次使用推荐）
python arxiv_tracker.py --interactive

# 命令行参数模式
python arxiv_tracker.py --categories cs.CV cs.LG --keywords "GPT" "LLM"

# 静默模式（适合定时任务）
python arxiv_tracker.py --config config.json --silent
```

---

## 配置说明

### 配置文件 (config.json)

```json
{
  "categories": ["cs.CV", "cs.LG", "cs.AI"],
  "keywords": ["deep learning", "transformer"],
  "keyword_fields": ["all:"],
  "max_results": 10,
  "output_dir": "outputs",
  "output_formats": ["console", "md", "json"],
  "history_file": "papers_history.json",
  "silent": false
}
```

| 配置项 | 说明 |
|-------|------|
| `categories` | arXiv分类，如 `cs.CV`(计算机视觉)、`cs.LG`(机器学习) |
| `keywords` | 搜索关键词列表 |
| `keyword_fields` | 搜索字段：`ti:`(标题)、`abs:`(摘要)、`all:`(全部) |
| `max_results` | 最大返回论文数 |
| `output_formats` | 输出格式：`console`、`txt`、`md`、`csv`、`json` |

### 常用arXiv分类

| 分类 | 说明 |
|-----|------|
| cs.CV | 计算机视觉 |
| cs.LG | 机器学习 |
| cs.AI | 人工智能 |
| cs.CL | 自然语言处理 |
| cs.CR | 密码学 |
| stat.ML | 统计机器学习 |

---

## 定时任务配置

使用系统Crontab实现定时抓取：

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天早上8点执行）
0 8 * * * /usr/bin/python3 /path/to/arxiv_tracker.py --config config.json --silent
```

---

## 项目结构

```
arxiv_paper_tracker/
├── arxiv_tracker.py      # 主程序
├── config.json           # 配置文件
├── requirements.txt      # 依赖列表
├── papers_history.json   # 历史记录（自动生成）
├── outputs/              # 输出目录
└── README.md
```

---

## 技术栈

| 功能 | 选用库 | 理由 |
|-----|-------|------|
| arXiv API | `arxiv` | 官方SDK |
| 数据处理 | `pandas` | 多格式导出 |
| 进度显示 | `tqdm` | 简洁易用 |
| 参数解析 | `argparse` | Python标准库 |
| 配置管理 | `json` | Python标准库 |

---

## 命令行参数

```
用法: arxiv_tracker.py [选项]

选项:
  -h, --help            显示帮助信息
  -c, --config CONFIG   配置文件路径
  --categories [CAT ...] arXiv分类
  --keywords [KW ...]   搜索关键词
  --keyword-fields {ti:,abs:,all:} [{ti:,abs:,all:} ...]
                        关键词搜索字段
  --max-results N       最大结果数 (默认: 10)
  -o, --output-dir DIR  输出目录 (默认: outputs)
  --output-formats {console,txt,md,csv,json} [{console,txt,md,csv,json} ...]
                        输出格式
  --history-file FILE   历史记录文件
  -s, --silent          静默模式
  -i, --interactive     交互式配置
  --no-verify-ssl       禁用SSL验证（用于网络环境问题）
```

---

## SSL连接问题解决

如果遇到SSL连接错误（常见于WSL2环境），可以使用以下方法解决：

### 方法1：禁用SSL验证（推荐）

```bash
python3 arxiv_tracker.py --config config.json --no-verify-ssl
```

### 方法2：更新系统证书

```bash
sudo apt-get update && sudo apt-get install ca-certificates
```

### 方法3：升级Python SSL相关包

```bash
pip3 install --upgrade certifi urllib3 requests
```

---

## 使用示例

### 示例1：追踪计算机视觉最新论文

```bash
python arxiv_tracker.py --categories cs.CV --max-results 20
```

### 示例2：搜索GPT相关论文

```bash
python arxiv_tracker.py --keywords "GPT" "LLM" --output-formats md csv
```

### 示例3：组合查询

```bash
python arxiv_tracker.py \
  --categories cs.CV cs.LG \
  --keywords "segmentation" "detection" \
  --max-results 15 \
  --output-formats console md json
```

---

## License

本项目采用 **CC-BY-NC 4.0** 许可证（署名-非商业性使用 4.0）

### 使用许可

- ✅ **允许**：共享、修改、使用本代码
- ⚠️ **要求**：使用时必须注明出处（署名）
- ❌ **禁止**：商业用途

### 署名示例

```
基于 arxiv-paper-tracker (https://github.com/hhhhxl/arxiv-paper-tracker)
原作者：hhhhxl
采用 CC-BY-NC 4.0 许可证
```

完整许可证内容：https://creativecommons.org/licenses/by-nc/4.0/deed.zh

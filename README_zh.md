<div align="center">

# Notion Researcher

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Notion API](https://img.shields.io/badge/Notion%20API-v2-000000?logo=notion&logoColor=white)](https://developers.notion.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**作者**: [AatroxChen77](https://github.com/AatroxChen77)

[English README](README.md)

</div>

---

<p align="center">
  <a href="#features">✨ 主要功能</a> •
  <a href="#installation">⚙️ 安装</a> •
  <a href="#usage">🚀 使用方法</a> •
  <a href="#architecture">🏗️ 项目架构</a>
</p>

## 📖 简介

**Notion Researcher** 是一个强大的 CLI 工具，旨在简化将本地 Markdown 文档同步到 Notion 的工作流程。

它解决了常见的“复制粘贴”格式问题，通过解析标准 Markdown 文件——包括 **表格**、**图片** 和 **LaTeX 公式** 等复杂元素——并自动将其作为格式完美的页面发布到您的 Notion 工作区。该工具专为喜欢本地编辑但需要集中、可共享知识库的研究人员和开发人员量身定制。

---

## <span id="features">✨ 主要功能</span>

- **🔬 高级 Markdown 解析**:
    - **智能表格处理**: 使用状态机稳健地解析 Markdown 表格 (GFM)，自动修复列对齐问题并填充缺失的单元格。
    - **LaTeX 支持**: 无缝转换行内 (`$E=mc^2$`) 和块级 (`$$...$$`) LaTeX 数学表达式为原生 Notion 公式块。
    - **富文本与图片**: 完美支持 **粗体**、*斜体* 以及标准图片语法 `![alt](url)`。
- **🔄 灵活的同步模式**:
    - **子页面创建**: 默认情况下，每次同步都会在配置的根页面下创建一个新的子页面。
    - **追加模式**: 使用 `--append` 参数可以将内容追加到现有页面的底部，而不是创建新页面。
- **🎯 精确控制**:
    - **目标覆盖**: 通过 CLI 直接指定目标页面 ID 或 URL (`--target`)，允许您同步到不同页面而无需修改 `config.yaml`。
    - **自动时间戳**: 如果未提供标题，则自动生成带时间戳的标题（例如 `2025-12-26 10:30 Log`）。
- **🔒 安全且可扩展**: 
    - 配置（API 令牌）通过 `config.yaml` 解耦。
    - 实现智能批处理（100 个块/请求），在处理大型文档时严格遵守 Notion API 限制。

---

## <span id="installation">⚙️ 安装</span>

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/AatroxChen77/notion-researcher.git
    cd notion-researcher
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置凭据**:
    运行工具一次以生成 `config.yaml` 模板，然后使用您的 Notion API 令牌和根页面 ID 进行编辑。
    ```bash
    python main.py dummy.md
    # 然后编辑 config.yaml:
    # notion_token: "ntn_..."
    # root_page_id: "..."
    ```

> 详细的 Token 和 Page ID 获取步骤，请参考 [Notion API 配置指南 (保姆级教程)](docs/Notion%20API%20配置指南%20(保姆级教程).md)。

---

## <span id="usage">🚀 使用方法</span>

### 1. 基础同步（新建子页面）
将文件同步为配置的根页面下的新页面。
```bash
python main.py notes.md --title "Research Weekly Report"
```
*如果省略 `--title`，将使用当前时间戳作为标题。*

### 2. 追加到现有页面
将内容追加到目标页面的底部，而不是创建新页面。
```bash
python main.py notes.md --append
```

### 3. 同步到指定目标
覆盖 `config.yaml` 中的 `root_page_id` 进行一次性同步。支持 ID 或完整 URL。
```bash
python main.py notes.md --target "https://www.notion.so/My-Page-1234567890abcdef"
```

### CLI 参数说明
| 参数 | 简写 | 说明 |
| :--- | :--- | :--- |
| `file` | - | Markdown 文件路径 (必填)。 |
| `--title` | `-t` | 新 Notion 页面的标题。 |
| `--target` | `-p` | 目标 Notion 页面 ID 或 URL (覆盖配置)。 |
| `--append` | `-a` | 追加到目标页面而不是创建子页面。 |

---

## <span id="architecture">🏗️ 项目架构</span>

本项目采用模块化结构以分离关注点：

```plaintext
.
├── config.yaml          # 用户配置 (Token & Page ID)
├── main.py              # CLI 入口点 (参数解析)
├── src/
│   ├── client.py        # NotionSync 类 (API 交互)
│   ├── parser.py        # 核心解析逻辑 (状态机)
│   └── utils.py         # 工具函数 (配置, 日志, ID 提取)
├── requirements.txt     # Python 依赖
└── README.md            # 项目文档
```

### 核心逻辑亮点
- **状态机解析**: `src/parser.py` 中的解析器使用 `while` 循环遍历行，允许它“向前查看”并消耗多行以处理表格和块级公式 (`$$`) 等结构。
- **依赖注入**: `main.py` 将配置和令牌注入 `NotionSync`，保持核心逻辑的可测试性并与 CLI 独立。

---

## 📜 许可证

本项目采用 MIT 许可证授权。

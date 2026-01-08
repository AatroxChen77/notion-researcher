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

**Notion Researcher** (CLI 命令: `np`) 是一个强大的工具，旨在自动化将本地 Markdown 文档同步到 Notion。它填补了本地编辑与 Notion 协作工作区之间的鸿沟，通过稳健地解析 Markdown（包括表格、LaTeX 公式、图片和超链接）并将其作为原生 Notion 块发布。

它解决了常见的“复制粘贴”格式问题，通过解析标准 Markdown 文件并自动将其作为格式完美的页面发布到您的 Notion 工作区。该工具专为喜欢本地编辑但需要集中、可共享知识库的研究人员和开发人员量身定制。

---

## <span id="features">✨ 主要功能</span>

- **🔬 高级 Markdown 解析**:
    - **智能表格处理**: 使用状态机稳健地解析 GFM 表格，自动修复列对齐问题并填充缺失的单元格。
    - **公式支持**: 无缝转换行内 (`$E=mc^2$`) 和块级 (`$$...$$`) LaTeX 数学表达式为原生 Notion 公式块。
    - **扩展标题**: 直接映射 H1-H3；自动将 H4-H6 映射为 Notion 的 Heading 3 以保持结构。
    - **列表与嵌套**: 支持无序/有序列表及 **隐式嵌套**（列表项后的段落自动作为子块嵌套）。
    - **噪声清洗**: 自动移除内容中常见的 OCR/PDF 伪影（如重复的 `1111`）。
    - **递归富文本**: 支持递归解析粗体、斜体、代码和链接（例如斜体中的**粗体**）。
- **🧠 智能 CLI**:
    - **URL 检测**: 自动检测第一个参数是否为 Notion URL/ID。如果未指定文件，默认将 `notes/tmp.md` 同步到该目标。
- **🔄 灵活的同步模式**:
    - **默认追加模式**: 默认情况下，将内容追加到目标页面的底部，非常适合日常日志。
    - **子页面创建**: 使用 `--new` (`-n`) 强制在配置的根数据库下创建一个新的子页面。
- **🎯 精确控制**:
    - **目标覆盖**: 通过 CLI 直接指定目标页面 ID 或 URL (`--target` / `-p`)，覆盖 `config.yaml`。
    - **快速失败**: 在发起任何 API 调用*之前*验证文件并解析 Markdown，防止部分同步。
- **🔒 安全且可扩展**:
    - **批处理**: 自动处理 Notion API 限制（每请求 100 个块）。
    - **配置解耦**: 凭据通过 `config.yaml` 管理。

---

## <span id="installation">⚙️ 安装</span>

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/AatroxChen77/notion-researcher.git
    cd notion-researcher
    ```

2.  **安装为包**:
    以可编辑模式安装包以启用 `np` 命令：
    ```bash
    pip install -e .
    ```

3.  **配置凭据**:
    运行工具一次以生成 `config.yaml` 模板，然后使用您的 Notion API 令牌和根页面 ID 进行编辑。
    ```bash
    np notes/tmp.md
    # 然后编辑 config.yaml:
    # notion_token: "ntn_..."
    # root_page_id: "..."
    ```

> 详细的 Token 和 Page ID 获取步骤，请参考 [Notion API 配置指南 (保姆级教程)](docs/Notion%20API%20配置指南%20(保姆级教程).md)。

---

## <span id="usage">🚀 使用方法</span>

安装完成后，使用 `np` 命令（`notion-pusher` 的缩写）同步您的文件。

### 1. 智能模式 (快速同步)
直接粘贴 Notion URL，将默认文件 (`notes/tmp.md`) 同步到该页面。
```bash
np https://www.notion.so/My-Page-1234567890abcdef
```

### 2. 基础同步（追加模式）
默认情况下，内容将追加到配置的根页面。
```bash
np notes.md
```

### 3. 创建新子页面
强制在根页面下创建一个新的子页面。
```bash
np notes.md --new --title "Research Weekly Report"
```
*如果省略 `--title`，将使用当前时间戳作为标题。*

### 4. 同步到指定目标
覆盖 `config.yaml` 中的 `root_page_id` 进行一次性同步。支持 ID 或完整 URL。
```bash
np notes.md --target "https://www.notion.so/My-Page-1234567890abcdef"
```

### CLI 参数说明
| 参数 | 简写 | 说明 |
| :--- | :--- | :--- |
| `file` | - | Markdown 文件路径 (或智能模式下的目标 URL)。 |
| `--title` | `-t` | 新 Notion 页面的标题。 |
| `--target` | `-p` | 目标 Notion 页面 ID 或 URL (覆盖配置)。 |
| `--new` | `-n` | 强制创建新子页面而不是追加 (默认为追加模式)。 |

---

## <span id="architecture">🏗️ 项目架构</span>

本项目采用模块化结构：

```plaintext
.
├── config.yaml          # 用户配置 (Token & Page ID)
├── main.py              # CLI 入口点 (智能 CLI & 快速失败验证)
├── src/
│   ├── client.py        # NotionSync (批处理 & API 封装)
│   ├── parser.py        # Markdown 解析器 (状态机 + 递归正则)
│   └── utils.py         # 工具函数 (日志, 配置, ID 提取)
├── setup.py             # 包配置 (定义 `np` 命令)
└── README.md            # 项目文档
```

### 核心组件
- **快速失败策略**: `main.py` 立即验证文件存在并解析内容，如果出错则在网络请求前中止。
- **状态机解析**: `src/parser.py` 使用状态机处理多行块（表格、公式），并使用带命名组的 `re.finditer` 处理行内元素。
- **递归下降**: 行内解析通过递归处理嵌套样式（例如斜体中的**粗体**）。
- **依赖注入**: 凭据和配置在运行时注入 `NotionSync`。

---

## 📜 许可证

本项目采用 MIT 许可证授权。

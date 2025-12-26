<div align="center">

# Notion Researcher

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**作者**: [AatroxChen77](https://github.com/AatroxChen77)

[English README](README.md)

</div>

---

<p align="center">
  <a href="#features">✨ 主要功能</a> •
  <a href="#installation">⚙️ 安装</a> •
  <a href="#usage">🚀 使用方法</a> •
  <a href="#logic">🧮 核心逻辑</a>
</p>

## 📖 简介

**Notion Researcher** 是一个强大的 CLI 工具，旨在简化将本地 Markdown 文档同步到 Notion 的工作流程。

它解决了常见的“复制粘贴”格式问题，通过解析标准 Markdown 文件——包括 **表格** 和 **LaTeX 公式** 等复杂元素——并自动将其作为格式完美的页面发布到您的 Notion 工作区。该工具专为喜欢本地编辑但需要集中、可共享知识库的研究人员和开发人员量身定制。

---

## <span id="features">✨ 主要功能</span>

- **🔬 高级 Markdown 解析**:
    - **智能表格处理**: 使用状态机稳健地解析 Markdown 表格，自动修复列对齐问题并填充缺失的单元格。
    - **LaTeX 支持**: 无缝转换行内 (`$E=mc^2$`) 和块级 (`$$...$$`) LaTeX 数学表达式为原生 Notion 公式块。
    - **富文本**: 在混合内容中保留 **粗体**、*斜体* 和其他标准格式。
- **📂 自动整理**:
    - **子页面创建**: 每次同步时自动在您的根数据库下创建一个新的子页面，保持工作区整洁有序。
    - **自动时间戳**: 如果未提供标题，则自动生成带时间戳的标题（例如 `2025-12-26 10:30 Log`）以便快速记录日志。
- **🔒 安全且可扩展**: 
    - 配置（API 令牌）通过 `config.yaml` 解耦。
    - 实现智能批处理（100 个块/请求），在处理大型文档时遵守 Notion API 限制。

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

---

## <span id="usage">🚀 使用方法</span>

### 1. 使用自定义标题同步
非常适合周报或文献综述：
```bash
python main.py notes.md --title "Research Weekly Report"
```

### 2. 快速同步（自动时间戳）
使用当前时间戳作为页面标题同步文件：
```bash
python main.py notes.md
```

---

## <span id="logic">🧮 核心逻辑</span>

### Markdown 解析逻辑

该工具的核心在于其 `NotionSync` 类，它将原始 Markdown 文本转换为结构化的 Notion 块。

#### 表格状态机
解析器实现了一个状态机来处理表格。它缓冲以 `|` 开头的行，计算最大列数 $C_{max}$，并归一化所有行 $R_i$ 使得：

$$ \text{len}(R_i) = C_{max} \quad \forall i \in \text{Table Rows} $$

这确保了即使对于格式错误的 Markdown 表格，也能满足 Notion 严格的块格式要求。

#### 公式与富文本解析
文本解析器使用基于优先级的正则方法。它首先隔离 LaTeX 表达式以防止格式误报：

1.  **提取公式**: `r'(\$[^\$]+\$)'`
2.  **提取粗体文本**: `r'(\*\*[^\*]+\*\*)'` (仅应用于非公式片段)

### 文件结构

```plaintext
.
├── config.yaml          # 用户配置 (Token & Page ID)
├── custom_push.py       # 旧版脚本 (保留供参考)
├── main.py              # 主 CLI 入口点和逻辑
├── notes.md             # 示例 Markdown 文件
├── requirements.txt     # Python 依赖
└── README.md            # 项目文档
```

---

## 📜 许可证

本项目采用 MIT 许可证授权。

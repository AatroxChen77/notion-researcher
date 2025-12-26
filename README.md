<div align="center">

# Notion Researcher

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Notion API](https://img.shields.io/badge/Notion%20API-v2-000000?logo=notion&logoColor=white)](https://developers.notion.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Author**: [AatroxChen77](https://github.com/AatroxChen77)

[中文说明](README_zh.md)

</div>

---

<p align="center">
  <a href="#features">✨ Key Features</a> •
  <a href="#installation">⚙️ Installation</a> •
  <a href="#usage">🚀 Usage</a> •
  <a href="#architecture">🏗️ Architecture</a>
</p>

## 📖 Introduction

**Notion Researcher** is a robust CLI tool designed to streamline the workflow of syncing local Markdown documentation to Notion.

It solves common "copy-paste" formatting issues by parsing standard Markdown files—including complex elements like **Tables**, **Images**, and **LaTeX equations**—and automatically publishing them as perfectly formatted pages in your Notion workspace. This tool is tailored for researchers and developers who prefer local editing but need a centralized, sharable knowledge base.

---

## <span id="features">✨ Key Features</span>

- **🔬 Advanced Markdown Parsing**:
    - **Smart Table Handling**: Uses a state machine to robustly parse Markdown tables (GFM), automatically fixing column alignment issues and padding missing cells.
    - **LaTeX Support**: Seamlessly converts inline (`$E=mc^2$`) and block (`$$...$$`) LaTeX math expressions into native Notion equation blocks.
    - **Rich Text & Images**: Preserves **bold**, *italic*, and standard image syntax `![alt](url)`.
- **🔄 Flexible Sync Modes**:
    - **Child Page Creation**: By default, creates a new child page under your root database for each sync.
    - **Append Mode**: Use the `--append` flag to add content to the bottom of an existing page instead of creating a new one.
- **🎯 Precise Control**:
    - **Target Override**: Specify a target Page ID or URL directly via CLI (`--target`), allowing you to sync to different pages without changing `config.yaml`.
    - **Auto-Timestamping**: If no title is provided, automatically generates a timestamped title (e.g., `2025-12-26 10:30 Log`).
- **🔒 Secure & Scalable**: 
    - Configuration (API Tokens) is decoupled via `config.yaml`.
    - Implements intelligent batching (100 blocks/request) to handle large documents while respecting Notion API limits.

---

## <span id="installation">⚙️ Installation</span>

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/AatroxChen77/notion-researcher.git
    cd notion-researcher
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Credentials**:
    Run the tool once to generate the `config.yaml` template, then edit it with your Notion API Token and Root Page ID.
    ```bash
    python main.py dummy.md
    # Then edit config.yaml:
    # notion_token: "ntn_..."
    # root_page_id: "..."
    ```

> For a detailed step-by-step guide on getting your Token and Page ID, please refer to the [Notion API Configuration Guide](docs/Notion%20API%20配置指南%20(保姆级教程).md).

---

## <span id="usage">🚀 Usage</span>

### 1. Basic Sync (New Child Page)
Syncs the file as a new page under the configured root page.
```bash
python main.py notes.md --title "Research Weekly Report"
```
*If `--title` is omitted, the current timestamp will be used.*

### 2. Append to Existing Page
Appends the content to the bottom of the target page instead of creating a new one.
```bash
python main.py notes.md --append
```

### 3. Sync to a Specific Target
Override the `root_page_id` in `config.yaml` for a one-off sync. Accepts ID or full URL.
```bash
python main.py notes.md --target "https://www.notion.so/My-Page-1234567890abcdef"
```

### CLI Arguments
| Argument | Short | Description |
| :--- | :--- | :--- |
| `file` | - | Path to the Markdown file (Required). |
| `--title` | `-t` | Title for the new Notion page. |
| `--target` | `-p` | Target Notion Page ID or URL (overrides config). |
| `--append` | `-a` | Append to target page instead of creating a child page. |

---

## <span id="architecture">🏗️ Architecture</span>

The project follows a modular structure to separate concerns:

```plaintext
.
├── config.yaml          # User configuration (Token & Page ID)
├── main.py              # Main CLI entry point (Argument Parsing)
├── src/
│   ├── client.py        # NotionSync class (API interactions)
│   ├── parser.py        # Core parsing logic (State Machine)
│   └── utils.py         # Helpers (Config, Logging, ID Extraction)
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

### Core Logic Highlights
- **State Machine Parsing**: The parser in `src/parser.py` iterates through lines using a `while` loop, allowing it to "look ahead" and consume multiple lines for blocks like Tables and Block Equations (`$$`).
- **Dependency Injection**: `main.py` injects configuration and tokens into `NotionSync`, keeping the core logic testable and independent of the CLI.

---

## 📜 License

This project is licensed under the MIT License.

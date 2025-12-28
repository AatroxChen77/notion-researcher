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

**Notion Researcher** (CLI command: `np`) is a tool that automates the syncing of local Markdown documentation to Notion. It bridges the gap between local editing and Notion's collaborative workspace by robustly parsing Markdown—including tables, LaTeX equations, images, and hyperlinks—and publishing them as native Notion blocks.

It solves common "copy-paste" formatting issues by parsing standard Markdown files and automatically publishing them as perfectly formatted pages in your Notion workspace. This tool is tailored for researchers and developers who prefer local editing but need a centralized, sharable knowledge base.

---

## <span id="features">✨ Key Features</span>

- **🔬 Advanced Markdown Parsing**:
    - **Smart Table Handling**: Uses a state machine to robustly parse GFM tables, fixing column alignment and padding missing cells.
    - **Math Support**: Seamlessly converts inline (`$E=mc^2$`) and block (`$$...$$`) LaTeX math expressions into native Notion equation blocks.
    - **Extended Headers**: Maps H1-H3 directly; automatically maps H4-H6 to Notion's Heading 3 to preserve structure.
    - **Lists & Nesting**: Supports bullet/numbered lists and **Implicit Nesting** (paragraphs under list items are automatically nested).
    - **Noise Cleaning**: Automatically removes common OCR/PDF artifacts (e.g., `1111`) from content.
    - **Rich Text**: Preserves bold, italic, code, and links.
- **🔄 Flexible Sync Modes**:
    - **Default Append Mode**: Appends content to the bottom of the target page, ideal for daily logging.
    - **Child Page Creation**: Use `--new` (`-n`) to create a new child page under your root database.
- **🎯 Precise Control**:
    - **Target Override**: Specify a target Page ID or URL via CLI (`--target` / `-p`), overriding `config.yaml`.
    - **Fail Fast**: Validates files and parses Markdown *before* any API calls to prevent partial syncs.
- **🔒 Secure & Scalable**:
    - **Batching**: Automatically handles Notion API limits (100 blocks per request).
    - **Configuration**: Credentials are decoupled via `config.yaml`.

---

## <span id="installation">⚙️ Installation</span>

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/AatroxChen77/notion-researcher.git
    cd notion-researcher
    ```

2.  **Install as a Package**:
    Install the package in editable mode to enable the `np` command:
    ```bash
    pip install -e .
    ```

3.  **Configure Credentials**:
    Run the tool once to generate the `config.yaml` template, then edit it with your Notion API Token and Root Page ID.
    ```bash
    np notes/tmp.md
    # Then edit config.yaml:
    # notion_token: "ntn_..."
    # root_page_id: "..."
    ```

> For a detailed guide on getting your Token and Page ID, please refer to the [Notion API Configuration Guide](docs/Notion%20API%20配置指南%20(保姆级教程).md).

---

## <span id="usage">🚀 Usage</span>

Once installed, use the `np` command (short for `notion-pusher`) to sync your files.

### 1. Basic Sync (Append Mode)
By default, content is appended to the configured root page.
```bash
np notes.md
```

### 2. Create New Child Page
Force the creation of a new child page under the root page.
```bash
np notes.md --new --title "Research Weekly Report"
```
*If `--title` is omitted, the current timestamp will be used.*

### 3. Sync to a Specific Target
Override the `root_page_id` in `config.yaml` for a one-off sync. Accepts ID or full URL.
```bash
np notes.md --target "https://www.notion.so/My-Page-1234567890abcdef"
```

### CLI Arguments
| Argument | Short | Description |
| :--- | :--- | :--- |
| `file` | - | Path to the Markdown file (Required). |
| `--title` | `-t` | Title for the new Notion page. |
| `--target` | `-p` | Target Notion Page ID or URL (overrides config). |
| `--new` | `-n` | Force create a new child page instead of appending (Default is Append). |

---

## <span id="architecture">🏗️ Architecture</span>

The project follows a modular structure:

```plaintext
.
├── config.yaml          # User configuration (Token & Page ID)
├── main.py              # CLI entry point (Fail Fast validation)
├── src/
│   ├── client.py        # NotionSync (Batching & API Wrapper)
│   ├── parser.py        # Markdown Parser (State Machine + Regex)
│   └── utils.py         # Utilities (Logging, Config, ID Extraction)
├── setup.py             # Package configuration (defines `np` command)
└── README.md            # Project documentation
```

### Key Components
- **Fail Fast Strategy**: `main.py` validates file existence and parses content immediately, aborting before any network requests if errors occur.
- **State Machine Parsing**: `src/parser.py` uses a state machine to handle multi-line blocks (Tables, Equations) and `re.finditer` with named groups for inline elements.
- **Dependency Injection**: Credentials and configuration are injected into `NotionSync` at runtime.

---

## 📜 License

This project is licensed under the MIT License.

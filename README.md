<div align="center">

# Notion Researcher

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Author**: [AatroxChen](https://github.com/AatroxChen)

</div>

---

<p align="center">
  <a href="#features">✨ Key Features</a> •
  <a href="#installation">⚙️ Installation</a> •
  <a href="#usage">🚀 Usage</a> •
  <a href="#logic">🧮 Core Logic</a>
</p>

## 📖 Introduction

**Notion Researcher** is a robust CLI tool designed to streamline the workflow of syncing local Markdown documentation to Notion. 

It solves the common "copy-paste" formatting issues by parsing standard Markdown files—including complex elements like **Tables** and **LaTeX equations**—and automatically publishing them as perfectly formatted pages in your Notion workspace. This tool is tailored for researchers and developers who prefer local editing but need a centralized, sharable knowledge base.

---

## <span id="features">✨ Key Features</span>

- **🔬 Advanced Markdown Parsing**:
    - **Smart Table Handling**: Uses a state machine to robustly parse Markdown tables, automatically fixing column alignment issues and padding missing cells.
    - **LaTeX Support**: Seamlessly converts inline (`$E=mc^2$`) and block (`$$...$$`) LaTeX math expressions into native Notion equation blocks.
    - **Rich Text**: Preserves **bold**, *italic*, and other standard formatting within mixed content.
- **📂 Automated Organization**:
    - **Child Page Creation**: Automatically creates a new child page under your root database for each sync, keeping your workspace organized.
    - **Auto-Timestamping**: If no title is provided, automatically generates a timestamped title (e.g., `2025-12-26 10:30 Log`) for quick journaling.
- **🔒 Secure & Scalable**: 
    - Configuration (API Tokens) is decoupled via `config.yaml`.
    - Implements intelligent batching (100 blocks/request) to handle large documents while respecting Notion API limits.

---

## <span id="installation">⚙️ Installation</span>

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/AatroxChen/notion-researcher.git
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

---

## <span id="usage">🚀 Usage</span>

### 1. Sync with Custom Title
Perfect for weekly reports or literature reviews:
```bash
python main.py notes.md --title "Research Weekly Report"
```

### 2. Quick Sync (Auto-Timestamp)
To sync a file using the current timestamp as the page title:
```bash
python main.py notes.md
```

---

## <span id="logic">🧮 Core Logic</span>

### Markdown Parsing Logic

The core of the tool lies in its `NotionSync` class, which transforms raw Markdown text into structured Notion blocks.

#### Table State Machine
The parser implements a state machine to handle tables. It buffers lines starting with `|`, calculates the maximum column count $C_{max}$, and normalizes all rows $R_i$ such that:

$$ \text{len}(R_i) = C_{max} \quad \forall i \in \text{Table Rows} $$

This ensures that Notion's strict block format requirements are met even for malformed Markdown tables.

#### Equation & Rich Text Parsing
The text parser uses a priority-based regex approach. It first isolates LaTeX expressions to prevent false positives in formatting:

1.  **Extract Equations**: `r'(\$[^\$]+\$)'`
2.  **Extract Bold Text**: `r'(\*\*[^\*]+\*\*)'` (applied only to non-equation segments)

### File Structure

```plaintext
.
├── config.yaml          # User configuration (Token & Page ID)
├── custom_push.py       # Legacy script (kept for reference)
├── main.py              # Main CLI entry point and logic
├── notes.md             # Example Markdown file
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## 📜 License

This project is licensed under the MIT License.

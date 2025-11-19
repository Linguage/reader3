# Reader3 项目概览

## 1. 项目简介
Reader3 是一个轻量级、可自托管的 EPUB 阅读器，设计用于逐章阅读 EPUB 电子书。它专为那些希望将文本内容复制到 LLM（大型语言模型）进行辅助阅读的用户进行了优化。

## 2. 项目结构

### 核心文件
- **`reader3.py`**: 核心处理脚本。
    - **功能**: 解析 EPUB 文件，提取元数据、目录 (TOC)、章节内容和图片。
    - **数据结构**: 定义了 `Book`、`BookMetadata`、`ChapterContent` 和 `TOCEntry`。
    - **输出**: 清理 HTML 内容（移除脚本、样式等），并将处理后的数据保存为 pickle 文件 (`book.pkl`) 存储在生成的数据目录中。
- **`server.py`**: Web 服务器应用程序。
    - **框架**: 基于 FastAPI 构建。
    - **功能**: 
        - 提供列出所有已处理书籍的图书馆视图。
        - 渲染书籍章节以供阅读。
        - 提供从书籍中提取的图片服务。
    - **端口**: 默认为 `8123`。
- **`templates/`**: 包含 Jinja2 HTML 模板。
    - `library.html`: 展示可用书籍列表的主页。
    - `reader.html`: 特定章节的阅读界面。

### 配置与依赖
- **`pyproject.toml` / `uv.lock`**: 项目依赖管理文件。本项目使用 `uv` 进行包管理。
- **`README.md`**: 基本项目文档。

## 3. 使用指南

### 前提条件
确保你已安装 `uv`（或者使用标准的 `pip` 安装 `pyproject.toml` 中列出的依赖，如 `ebooklib`、`beautifulsoup4`、`fastapi`、`uvicorn`、`jinja2`）。

### 第一步：处理 EPUB 电子书
要将书籍导入图书馆，首先需要处理 `.epub` 文件。

```bash
uv run reader3.py <filename.epub>
```
*示例：*
```bash
uv run reader3.py dracula.epub
```
**结果**: 这将创建一个名为 `<filename>_data`（例如 `dracula_data`）的目录，其中包含：
- `book.pkl`: 序列化后的已处理书籍数据。
- `images/`: 一个包含从书籍中提取的图片的文件夹。

### 第二步：启动 Web 服务器
处理完一本或多本书籍后，启动 Web 服务器以进行查看。

```bash
uv run server.py
```

### 第三步：访问阅读器
打开你的浏览器并访问：
**http://localhost:8123**

- **图书馆视图**: 你将看到所有已处理书籍的列表。
- **阅读**: 点击一本书开始阅读。使用界面在章节之间导航。
- **复制**: 干净的文本格式使得能够轻松地将章节内容复制粘贴到其他工具中。

## 4. 数据管理
- **添加书籍**: 对新的 EPUB 文件运行 `reader3.py`。
- **删除书籍**: 只需删除生成的 `<filename>_data` 目录。

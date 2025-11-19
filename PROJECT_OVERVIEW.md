# Reader3 Project Overview

## 1. Project Introduction
Reader3 is a lightweight, self-hosted EPUB reader designed to read EPUB books chapter by chapter. It is particularly optimized for users who want to copy text content to LLMs (Large Language Models) for auxiliary reading.

## 2. Project Structure

### Core Files
- **`reader3.py`**: The core processing script.
    - **Functionality**: Parses EPUB files, extracts metadata, table of contents (TOC), chapter content, and images.
    - **Data Structures**: Defines `Book`, `BookMetadata`, `ChapterContent`, and `TOCEntry`.
    - **Output**: Cleans HTML content (removing scripts, styles, etc.) and saves the processed data as a pickle file (`book.pkl`) in a generated data directory.
- **`server.py`**: The web server application.
    - **Framework**: Built with FastAPI.
    - **Functionality**: 
        - Serves the library view listing all processed books.
        - Renders book chapters for reading.
        - Serves images extracted from the books.
    - **Port**: Defaults to `8123`.
- **`templates/`**: Contains Jinja2 HTML templates.
    - `library.html`: The home page showing the list of available books.
    - `reader.html`: The reading interface for a specific chapter.

### Configuration & Dependencies
- **`pyproject.toml` / `uv.lock`**: Project dependency management files. The project uses `uv` for package management.
- **`README.md`**: Basic project documentation.

## 3. Usage Guide

### Prerequisites
Ensure you have `uv` installed (or use standard `pip` to install dependencies listed in `pyproject.toml` such as `ebooklib`, `beautifulsoup4`, `fastapi`, `uvicorn`, `jinja2`).

### Step 1: Process an EPUB Book
To import a book into the library, you need to process the `.epub` file first.

```bash
uv run reader3.py <filename.epub>
```
*Example:*
```bash
uv run reader3.py dracula.epub
```
**Result**: This will create a directory named `<filename>_data` (e.g., `dracula_data`) containing:
- `book.pkl`: The serialized processed book data.
- `images/`: A folder containing extracted images from the book.

### Step 2: Start the Web Server
Once you have processed one or more books, start the web server to view them.

```bash
uv run server.py
```

### Step 3: Access the Reader
Open your web browser and navigate to:
**http://localhost:8123**

- **Library View**: You will see a list of all processed books.
- **Reading**: Click on a book to start reading. Use the interface to navigate between chapters.
- **Copying**: The clean text format makes it easy to copy-paste chapter content into other tools.

## 4. Data Management
- **Adding Books**: Run `reader3.py` on a new EPUB file.
- **Removing Books**: Simply delete the generated `<filename>_data` directory.

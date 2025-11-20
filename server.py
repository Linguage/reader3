import os
import pickle
import shutil
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from reader3 import Book, BookMetadata, ChapterContent, TOCEntry, process_epub, process_markdown, save_to_pickle

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")

# Where are the book folders located?
# Original EPUBs live in books/hub, processed *_data folders in books/shelf.
BASE_BOOKS_DIR = "books"
BOOKS_HUB_DIR = os.path.join(BASE_BOOKS_DIR, "hub")
BOOKS_SHELF_DIR = os.path.join(BASE_BOOKS_DIR, "shelf")

os.makedirs(BOOKS_HUB_DIR, exist_ok=True)
os.makedirs(BOOKS_SHELF_DIR, exist_ok=True)

@lru_cache(maxsize=10)
def load_book_cached(folder_name: str) -> Optional[Book]:
    """Loads the book from the pickle file under books/shelf.
    Cached so we don't re-read the disk on every click.
    """
    file_path = os.path.join(BOOKS_SHELF_DIR, folder_name, "book.pkl")
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "rb") as f:
            book = pickle.load(f)
        return book
    except Exception as e:
        print(f"Error loading book {folder_name}: {e}")
        return None

@app.post("/api/upload_epub")
async def upload_epub(
    file: UploadFile = File(...),
    split_level: int = Form(2),
):
    filename = os.path.basename(file.filename) if file.filename else "uploaded.epub"
    if not filename.lower().endswith(".epub"):
        filename = filename + ".epub"
    base_name, _ = os.path.splitext(filename)
    folder_name = base_name + "_data"
    epub_path = os.path.join(BOOKS_HUB_DIR, filename)
    out_dir = os.path.join(BOOKS_SHELF_DIR, folder_name)

    content = await file.read()
    with open(epub_path, "wb") as f:
        f.write(content)

    # Clamp split_level to [1, 6]
    if split_level < 1:
        split_level = 1
    elif split_level > 6:
        split_level = 6

    # Call process_epub with explicit split_level so it does not rely on env.
    book = process_epub(epub_path, out_dir, split_level=split_level)
    save_to_pickle(book, out_dir)
    load_book_cached.cache_clear()

    return {
        "status": "ok",
        "book_id": folder_name,
        "title": book.metadata.title,
        "split_level": book.split_level,
    }


@app.post("/api/upload_md")
async def upload_md(
    file: UploadFile = File(...),
):
    filename = os.path.basename(file.filename) if file.filename else "uploaded.md"
    lower = filename.lower()
    if not (lower.endswith(".md") or lower.endswith(".markdown")):
        filename = filename + ".md"
    base_name, _ = os.path.splitext(filename)
    folder_name = base_name + "_data"
    md_path = os.path.join(BOOKS_HUB_DIR, filename)
    out_dir = os.path.join(BOOKS_SHELF_DIR, folder_name)

    content = await file.read()
    with open(md_path, "wb") as f:
        f.write(content)

    book = process_markdown(md_path, out_dir)
    save_to_pickle(book, out_dir)
    load_book_cached.cache_clear()

    return {
        "status": "ok",
        "book_id": folder_name,
        "title": book.metadata.title,
        "split_level": book.split_level,
    }


@app.post("/api/books/{book_id}/delete")
async def delete_book(book_id: str):
    safe_id = os.path.basename(book_id)
    folder_path = os.path.join(BOOKS_SHELF_DIR, safe_id)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Book folder not found")

    if not safe_id.endswith("_data"):
        raise HTTPException(status_code=400, detail="Refusing to delete non-data folder")

    try:
        shutil.rmtree(folder_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete book folder: {e}")

    load_book_cached.cache_clear()

    return {"status": "ok", "book_id": safe_id}


@app.post("/api/books/{book_id}/resplit")
async def resplit_book(book_id: str, split_level: int = Form(2)):
    safe_id = os.path.basename(book_id)
    folder_path = os.path.join(BOOKS_SHELF_DIR, safe_id)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Book folder not found")

    book = load_book_cached(safe_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    source_path = os.path.join(BOOKS_HUB_DIR, book.source_file)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Source file not found in hub")

    ext = os.path.splitext(book.source_file)[1].lower()

    if ext == ".epub":
        if split_level < 1:
            split_level = 1
        elif split_level > 6:
            split_level = 6
        new_book = process_epub(source_path, folder_path, split_level=split_level)
    elif ext in (".md", ".markdown"):
        new_book = process_markdown(source_path, folder_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported source file type for resplit")

    save_to_pickle(new_book, folder_path)
    load_book_cached.cache_clear()

    return {
        "status": "ok",
        "book_id": safe_id,
        "title": new_book.metadata.title,
        "split_level": new_book.split_level,
        "chapters": len(new_book.spine),
    }


@app.post("/api/hub/import")
async def import_from_hub(filename: str = Form(...), split_level: int = Form(2)):
    """Import or re-import an EPUB that already exists in books/hub into books/shelf."""
    safe_name = os.path.basename(filename)
    if not safe_name.lower().endswith(".epub"):
        safe_name = safe_name + ".epub"

    epub_path = os.path.join(BOOKS_HUB_DIR, safe_name)
    if not os.path.exists(epub_path):
        raise HTTPException(status_code=404, detail="EPUB not found in hub")

    base_name, _ = os.path.splitext(safe_name)
    folder_name = base_name + "_data"
    out_dir = os.path.join(BOOKS_SHELF_DIR, folder_name)

    if split_level < 1:
        split_level = 1
    elif split_level > 6:
        split_level = 6

    book = process_epub(epub_path, out_dir, split_level=split_level)

    save_to_pickle(book, out_dir)
    load_book_cached.cache_clear()

    return {
        "status": "ok",
        "book_id": folder_name,
        "title": book.metadata.title,
        "split_level": book.split_level,
        "chapters": len(book.spine),
    }

@app.get("/", response_class=HTMLResponse)
async def library_view(request: Request):
    """Lists all available processed books."""
    books = []

    # Scan books/shelf for folders ending in '_data' that have a book.pkl
    if os.path.exists(BOOKS_SHELF_DIR):
        for item in os.listdir(BOOKS_SHELF_DIR):
            if not item.endswith("_data"):
                continue

            folder_path = os.path.join(BOOKS_SHELF_DIR, item)
            if not os.path.isdir(folder_path):
                continue

            # Try to load it to get the title
            book = load_book_cached(item)
            if book:
                books.append({
                    "id": item,
                    "title": book.metadata.title,
                    "author": ", ".join(book.metadata.authors),
                    "chapters": len(book.spine),
                    "split_level": getattr(book, "split_level", 1),
                })

    # List EPUB files in books/hub for management
    hub_files = []
    if os.path.exists(BOOKS_HUB_DIR):
        for fname in os.listdir(BOOKS_HUB_DIR):
            if not fname.lower().endswith(".epub"):
                continue
            base_name, _ = os.path.splitext(fname)
            shelf_id = base_name + "_data"
            matching = next((b for b in books if b["id"] == shelf_id), None)
            hub_files.append({
                "filename": fname,
                "shelf_id": shelf_id,
                "in_shelf": matching is not None,
                "title": matching["title"] if matching else None,
            })

    return templates.TemplateResponse("library.html", {"request": request, "books": books, "hub_files": hub_files})

@app.get("/read/{book_id}", response_class=HTMLResponse)
async def redirect_to_first_chapter(book_id: str):
    """Helper to just go to chapter 0."""
    return await read_chapter(book_id=book_id, chapter_index=0)

@app.get("/read/{book_id}/{chapter_index}", response_class=HTMLResponse)
async def read_chapter(request: Request, book_id: str, chapter_index: int):
    """The main reader interface."""
    book = load_book_cached(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if chapter_index < 0 or chapter_index >= len(book.spine):
        raise HTTPException(status_code=404, detail="Chapter not found")

    current_chapter = book.spine[chapter_index]

    # Calculate Prev/Next links
    prev_idx = chapter_index - 1 if chapter_index > 0 else None
    next_idx = chapter_index + 1 if chapter_index < len(book.spine) - 1 else None

    return templates.TemplateResponse("reader.html", {
        "request": request,
        "book": book,
        "current_chapter": current_chapter,
        "chapter_index": chapter_index,
        "book_id": book_id,
        "prev_idx": prev_idx,
        "next_idx": next_idx
    })

@app.get("/read/{book_id}/images/{image_name}")
async def serve_image(book_id: str, image_name: str):
    """
    Serves images specifically for a book.
    The HTML contains <img src="images/pic.jpg">.
    The browser resolves this to /read/{book_id}/images/pic.jpg.
    """
    # Security check: ensure book_id is clean
    safe_book_id = os.path.basename(book_id)
    safe_image_name = os.path.basename(image_name)

    img_path = os.path.join(BOOKS_SHELF_DIR, safe_book_id, "images", safe_image_name)

    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(img_path)

if __name__ == "__main__":
    import uvicorn
    print("Starting server at http://127.0.0.1:8123")
    uvicorn.run(app, host="127.0.0.1", port=8123)

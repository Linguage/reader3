"""
Parses an EPUB file into a structured object that can be used to serve the book via a web interface.
"""

import os
import pickle
import re
import shutil
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import unquote

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, Comment, Tag
import markdown as md_lib

# --- Data structures ---

@dataclass
class ChapterContent:
    """
    Represents a physical file in the EPUB (Spine Item).
    A single file might contain multiple logical chapters (TOC entries).
    """
    id: str           # Internal ID (e.g., 'item_1')
    href: str         # Filename (e.g., 'part01.html')
    title: str        # Best guess title from file
    content: str      # Cleaned HTML with rewritten image paths
    text: str         # Plain text for search/LLM context
    order: int        # Linear reading order


@dataclass
class TOCEntry:
    """Represents a logical entry in the navigation sidebar."""
    title: str
    href: str         # original href (e.g., 'part01.html#chapter1')
    file_href: str    # just the filename (e.g., 'part01.html')
    anchor: str       # just the anchor (e.g., 'chapter1'), empty if none
    children: List['TOCEntry'] = field(default_factory=list)
    depth: int = 0
    chapter_index: Optional[int] = None


@dataclass
class BookMetadata:
    """Metadata"""
    title: str
    language: str
    authors: List[str] = field(default_factory=list)
    description: Optional[str] = None
    publisher: Optional[str] = None
    date: Optional[str] = None
    identifiers: List[str] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)


@dataclass
class Book:
    """The Master Object to be pickled."""
    metadata: BookMetadata
    spine: List[ChapterContent]  # The actual content (linear files)
    toc: List[TOCEntry]          # The navigation tree
    images: Dict[str, str]       # Map: original_path -> local_path

    # Meta info
    source_file: str
    processed_at: str
    anchor_map: Dict[str, int] = field(default_factory=dict)
    split_level: int = 1
    version: str = "3.1"


# --- Utilities ---

def clean_html_content(soup: BeautifulSoup) -> BeautifulSoup:

    # Remove dangerous/useless tags
    for tag in soup(['script', 'style', 'iframe', 'video', 'nav', 'form', 'button']):
        tag.decompose()

    # Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove input tags
    for tag in soup.find_all('input'):
        tag.decompose()

    return soup


def extract_plain_text(soup: BeautifulSoup) -> str:
    """Extract clean text for LLM/Search usage."""
    text = soup.get_text(separator=' ')
    # Collapse whitespace
    return ' '.join(text.split())


def register_anchors_from_soup(soup: BeautifulSoup, file_name: str, order: int, anchor_map: Dict[str, int]):
    """Register anchors for both full path and basename variants.

    Some EPUB TOC hrefs use shortened paths (e.g. "Text/ch01.xhtml#foo") while
    spine item names may include a longer prefix (e.g. "OEBPS/Text/ch01.xhtml").
    To make lookups robust we register both variants.
    """
    basename = os.path.basename(file_name)

    for el in soup.find_all(attrs={"id": True}):
        anchor_id = el.get("id")
        if not anchor_id:
            continue
        full_key = f"{file_name}#{anchor_id}"
        base_key = f"{basename}#{anchor_id}"
        if full_key not in anchor_map:
            anchor_map[full_key] = order
        if base_key not in anchor_map:
            anchor_map[base_key] = order


def parse_toc_recursive(toc_list, depth=0) -> List[TOCEntry]:
    """
    Recursively parses the TOC structure from ebooklib.
    """
    result = []

    for item in toc_list:
        # ebooklib TOC items are either `Link` objects or tuples (Section, [Children])
        if isinstance(item, tuple):
            section, children = item
            entry = TOCEntry(
                title=section.title,
                href=section.href,
                file_href=section.href.split('#')[0],
                anchor=section.href.split('#')[1] if '#' in section.href else "",
                children=parse_toc_recursive(children, depth + 1),
                depth=depth,
            )
            result.append(entry)
        elif isinstance(item, epub.Link):
            entry = TOCEntry(
                title=item.title,
                href=item.href,
                file_href=item.href.split('#')[0],
                anchor=item.href.split('#')[1] if '#' in item.href else "",
                depth=depth,
            )
            result.append(entry)
        # Note: ebooklib sometimes returns direct Section objects without children
        elif isinstance(item, epub.Section):
             entry = TOCEntry(
                title=item.title,
                href=item.href,
                file_href=item.href.split('#')[0],
                anchor=item.href.split('#')[1] if '#' in item.href else "",
                depth=depth,
            )
             result.append(entry)

    return result


def get_fallback_toc(book_obj) -> List[TOCEntry]:
    """
    If TOC is missing, build a flat one from the Spine.
    """
    toc = []
    for item in book_obj.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            name = item.get_name()
            # Try to guess a title from the content or ID
            title = item.get_name().replace('.html', '').replace('.xhtml', '').replace('_', ' ').title()
            toc.append(TOCEntry(title=title, href=name, file_href=name, anchor=""))
    return toc


def extract_metadata_robust(book_obj) -> BookMetadata:
    """
    Extracts metadata handling both single and list values.
    """
    def get_list(key):
        data = book_obj.get_metadata('DC', key)
        return [x[0] for x in data] if data else []

    def get_one(key):
        data = book_obj.get_metadata('DC', key)
        return data[0][0] if data else None

    return BookMetadata(
        title=get_one('title') or "Untitled",
        language=get_one('language') or "en",
        authors=get_list('creator'),
        description=get_one('description'),
        publisher=get_one('publisher'),
        date=get_one('date'),
        identifiers=get_list('identifier'),
        subjects=get_list('subject')
    )


def _resolve_toc_entry_index(entry: TOCEntry, anchor_map: Dict[str, int]) -> Optional[int]:
    """Resolve which spine index a TOC entry should point to using anchor_map.

    We try several key variants to be robust against path differences, mimicking
    the logic used on the frontend (full path, basename, with/without anchor).
    """

    if not anchor_map:
        return None

    file_href = entry.file_href or ""
    anchor = entry.anchor or ""
    basename = os.path.basename(file_href) if file_href else ""

    candidates = []

    # If there is an explicit anchor, prefer anchor-based lookups.
    if anchor:
        if entry.href:
            candidates.append(entry.href)
        if file_href:
            candidates.append(f"{file_href}#{anchor}")
        if basename:
            candidates.append(f"{basename}#{anchor}")

    # Fallback: file-level keys.
    if file_href:
        candidates.append(file_href)
    if basename:
        candidates.append(basename)

    for key in candidates:
        if key in anchor_map:
            return anchor_map[key]

    return None


def attach_chapter_indices_to_toc(
    toc_entries: List[TOCEntry],
    anchor_map: Dict[str, int],
    max_depth: Optional[int] = None,
    _ancestors: Optional[List[TOCEntry]] = None,
) -> None:
    """Populate chapter_index for each TOCEntry using anchor_map.

    max_depth 决定“哪些 TOC 层级拥有独立页面”：
    - depth <= max_depth: 优先使用自身解析到的章节索引。
    - depth > max_depth: 继承最近的上级（depth <= max_depth 且 chapter_index 不为 None）的索引，
      这样深层小节在同一页面内通过锚点定位，而不是再拆出新页。

    如果 max_depth 为 None，则行为与旧版完全一致：所有节点都尽量解析自己的章节索引。
    """

    if _ancestors is None:
        _ancestors = []

    for entry in toc_entries:
        # 1) 先解析自身能落在哪个物理章节
        entry.chapter_index = _resolve_toc_entry_index(entry, anchor_map)

        # 2) 如果设置了 max_depth，且当前节点比该深度更深，
        #    则尝试继承最近的浅层祖先的 chapter_index。
        if max_depth is not None and entry.depth > max_depth:
            for anc in reversed(_ancestors):
                if anc.chapter_index is not None and anc.depth <= max_depth:
                    entry.chapter_index = anc.chapter_index
                    break

        # 3) 递归处理子节点，当前节点作为祖先传下去
        new_ancestors = _ancestors + [entry]
        if entry.children:
            attach_chapter_indices_to_toc(entry.children, anchor_map, max_depth=max_depth, _ancestors=new_ancestors)


# --- Main Conversion Logic ---

def process_epub(epub_path: str, output_dir: str, split_level: Optional[int] = None) -> Book:

    # 1. Load Book
    print(f"Loading {epub_path}...")
    book = epub.read_epub(epub_path)

    # 2. Extract Metadata
    metadata = extract_metadata_robust(book)

    # Determine heading split level (1-6) for logical chapter splitting.
    # Priority:
    #   1) explicit split_level argument from caller (API)
    #   2) READER3_SPLIT_HEADING_LEVEL env var (CLI / legacy)
    #   3) fallback default = 2
    if split_level is None:
        try:
            split_level = int(os.getenv("READER3_SPLIT_HEADING_LEVEL", "2"))
        except ValueError:
            split_level = 2
    else:
        try:
            split_level = int(split_level)
        except ValueError:
            split_level = 2

    if split_level < 1:
        split_level = 1
    elif split_level > 6:
        split_level = 6

    # 3. Prepare Output Directories
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    # 4. Extract Images & Build Map
    print("Extracting images...")
    image_map = {} # Key: internal_path, Value: local_relative_path

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_IMAGE:
            # Normalize filename
            original_fname = os.path.basename(item.get_name())
            # Sanitize filename for OS
            safe_fname = "".join([c for c in original_fname if c.isalpha() or c.isdigit() or c in '._-']).strip()

            # Save to disk
            local_path = os.path.join(images_dir, safe_fname)
            with open(local_path, 'wb') as f:
                f.write(item.get_content())

            # Map keys: We try both the full internal path and just the basename
            # to be robust against messy HTML src attributes
            rel_path = f"images/{safe_fname}"
            image_map[item.get_name()] = rel_path
            image_map[original_fname] = rel_path

    # 5. Process TOC
    print("Parsing Table of Contents...")
    toc_structure = parse_toc_recursive(book.toc)
    if not toc_structure:
        print("Warning: Empty TOC, building fallback from Spine...")
        toc_structure = get_fallback_toc(book)

    # 6. Process Content (Spine-based to preserve HTML validity)
    print("Processing chapters...")
    spine_chapters = []
    anchor_map: Dict[str, int] = {}

    # We iterate over the spine (linear reading order)
    order_counter = 0
    for i, spine_item in enumerate(book.spine):
        item_id, linear = spine_item
        item = book.get_item_with_id(item_id)

        if not item:
            continue

        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # Raw content
            raw_content = item.get_content().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(raw_content, 'html.parser')

            # A. Fix Images
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if not src:
                    continue

                # Decode URL (part01/image%201.jpg -> part01/image 1.jpg)
                src_decoded = unquote(src)
                filename = os.path.basename(src_decoded)

                # Try to find in map
                if src_decoded in image_map:
                    img['src'] = image_map[src_decoded]
                elif filename in image_map:
                    img['src'] = image_map[filename]

            # B. Clean HTML
            soup = clean_html_content(soup)

            # C. Extract Body Content only
            body = soup.find('body')
            content_root = body if body else soup

            full_html = "".join(str(x) for x in content_root.contents)

            segments = []
            if split_level >= 1:
                pattern = re.compile(
                    r"(<h([1-{}])[^>]*>.*?</h\\2>)".format(split_level),
                    flags=re.IGNORECASE | re.DOTALL,
                )
                matches = list(pattern.finditer(full_html))
                if not matches:
                    segments.append((None, full_html))
                else:
                    first_start = matches[0].start()
                    if first_start > 0:
                        pre_html = full_html[:first_start]
                        if pre_html.strip():
                            segments.append((None, pre_html))
                    for idx_m, m in enumerate(matches):
                        start = m.start()
                        end = matches[idx_m + 1].start() if idx_m + 1 < len(matches) else len(full_html)
                        seg_html = full_html[start:end]
                        heading_html = m.group(1)
                        heading_soup = BeautifulSoup(heading_html, 'html.parser')
                        heading_text = heading_soup.get_text(separator=" ", strip=True) or None
                        segments.append(heading_text and (heading_text, seg_html) or (None, seg_html))
            else:
                segments.append((None, full_html))

            print(f"[reader3] split_level={split_level}, file={item.get_name()}, segments={len(segments) if segments else 0}")

            if not segments or len(segments) == 1:
                final_html = segments[0][1] if segments else full_html
                section_soup = BeautifulSoup(final_html, 'html.parser')
                chapter = ChapterContent(
                    id=item_id,
                    href=item.get_name(),
                    title=f"Section {order_counter+1}",
                    content=final_html,
                    text=extract_plain_text(section_soup),
                    order=order_counter
                )
                spine_chapters.append(chapter)
                register_anchors_from_soup(section_soup, item.get_name(), order_counter, anchor_map)
                fname = item.get_name()
                base = os.path.basename(fname)
                if fname not in anchor_map:
                    anchor_map[fname] = order_counter
                if base not in anchor_map:
                    anchor_map[base] = order_counter
                order_counter += 1
            else:
                for seg_idx, (seg_title, seg_html) in enumerate(segments):
                    final_html = seg_html
                    section_soup = BeautifulSoup(final_html, 'html.parser')
                    chapter = ChapterContent(
                        id=f"{item_id}_{seg_idx}",
                        href=item.get_name(),
                        title=seg_title or f"Section {order_counter+1}",
                        content=final_html,
                        text=extract_plain_text(section_soup),
                        order=order_counter
                    )
                    spine_chapters.append(chapter)
                    register_anchors_from_soup(section_soup, item.get_name(), order_counter, anchor_map)
                    if seg_idx == 0:
                        fname = item.get_name()
                        base = os.path.basename(fname)
                        if fname not in anchor_map:
                            anchor_map[fname] = order_counter
                        if base not in anchor_map:
                            anchor_map[base] = order_counter
                    order_counter += 1

    # 7. Attach TOC → chapter index mapping now that anchor_map is complete.
    #    这里使用 split_level 作为“最大 TOC 深度”，决定哪些目录层级拥有独立页面。
    attach_chapter_indices_to_toc(toc_structure, anchor_map, max_depth=split_level)

    # 8. Final Assembly
    final_book = Book(
        metadata=metadata,
        spine=spine_chapters,
        toc=toc_structure,
        images=image_map,
        source_file=os.path.basename(epub_path),
        processed_at=datetime.now().isoformat(),
        anchor_map=anchor_map,
        split_level=split_level,
    )

    return final_book


def process_markdown(md_path: str, output_dir: str, split_level: Optional[int] = None) -> Book:
    print(f"Loading markdown {md_path}...")
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    if split_level is None:
        split_level = 2
    try:
        split_level = int(split_level)
    except (TypeError, ValueError):
        split_level = 2
    if split_level < 1:
        split_level = 1
    elif split_level > 6:
        split_level = 6

    title: Optional[str] = None
    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip() or None
            if title:
                break

    if not title:
        title = os.path.splitext(os.path.basename(md_path))[0] or "Untitled"

    metadata = BookMetadata(
        title=title,
        language="en",
        authors=[],
        description=None,
        publisher=None,
        date=None,
        identifiers=[],
        subjects=[],
    )

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    html = md_lib.markdown(
        md_text,
        extensions=[
            "fenced_code",
            "tables",
            "toc",
            "attr_list",
        ],
    )

    soup = BeautifulSoup(html, "html.parser")
    soup = clean_html_content(soup)

    body = soup.body if soup.body is not None else soup

    segments_html: List[str] = []
    segment_titles: List[Optional[str]] = []
    segment_anchors: List[Optional[str]] = []
    segment_levels: List[Optional[int]] = []

    current_nodes: List[Any] = []
    current_title: Optional[str] = None
    current_anchor: Optional[str] = None
    current_level: Optional[int] = None
    used_ids: Dict[str, bool] = {}
    heading_levels = {f"h{i}": i for i in range(1, 7)}

    def flush_segment() -> None:
        nonlocal current_nodes, current_title, current_anchor, current_level
        if not current_nodes:
            current_nodes = []
            return
        html_seg = "".join(str(n) for n in current_nodes)
        segments_html.append(html_seg)
        segment_titles.append(current_title)
        segment_anchors.append(current_anchor)
        segment_levels.append(current_level)
        current_nodes = []
        current_title = None
        current_anchor = None
        current_level = None

    for node in body.children:
        if isinstance(node, str):
            if not node.strip() and not current_nodes:
                continue
            current_nodes.append(node)
            continue
        if isinstance(node, Comment):
            continue
        if isinstance(node, Tag) and node.name in heading_levels:
            level = heading_levels[node.name]
            if level <= split_level:
                flush_segment()
                heading_text = node.get_text(separator=" ", strip=True) or None
                if heading_text is None:
                    continue
                anchor = node.get("id")
                if not anchor:
                    base = re.sub(r"[^a-zA-Z0-9]+", "-", heading_text).strip("-").lower() or "section"
                    anchor = base
                    counter = 2
                    while anchor in used_ids:
                        anchor = f"{base}-{counter}"
                        counter += 1
                    node["id"] = anchor
                used_ids[anchor] = True
                current_title = heading_text
                current_anchor = anchor
                current_level = level
                current_nodes.append(node)
                continue
            # heading deeper than split level -> do not start new segment, keep inline
            current_nodes.append(node)
            continue
        else:
            current_nodes.append(node)

    flush_segment()

    file_name = "index.html"

    if not segments_html:
        full_html = str(body)
        chapter_id = "markdown_0"
        section_soup = BeautifulSoup(full_html, "html.parser")
        text = extract_plain_text(section_soup)
        spine_chapters: List[ChapterContent] = [
            ChapterContent(
                id=chapter_id,
                href=file_name,
                title=title,
                content=full_html,
                text=text,
                order=0,
            )
        ]
        anchor_map: Dict[str, int] = {}
        register_anchors_from_soup(section_soup, file_name, 0, anchor_map)
        base = os.path.basename(file_name)
        if file_name not in anchor_map:
            anchor_map[file_name] = 0
        if base not in anchor_map:
            anchor_map[base] = 0
        toc_entries: List[TOCEntry] = [
            TOCEntry(
                title=title,
                href=file_name,
                file_href=file_name,
                anchor="",
                depth=0,
            )
        ]
    else:
        spine_chapters = []
        anchor_map = {}
        for idx, html_seg in enumerate(segments_html):
            seg_html = html_seg
            section_soup = BeautifulSoup(seg_html, "html.parser")
            seg_title = segment_titles[idx] or f"Section {idx + 1}"
            text = extract_plain_text(section_soup)
            chapter = ChapterContent(
                id=f"markdown_{idx}",
                href=file_name,
                title=seg_title,
                content=seg_html,
                text=text,
                order=idx,
            )
            spine_chapters.append(chapter)
            register_anchors_from_soup(section_soup, file_name, idx, anchor_map)
            fname = file_name
            base = os.path.basename(fname)
            if fname not in anchor_map:
                anchor_map[fname] = idx
            if base not in anchor_map:
                anchor_map[base] = idx

        toc_entries: List[TOCEntry] = []
        stack: List[Any] = []
        for idx in range(len(segments_html)):
            seg_title = segment_titles[idx] or f"Section {idx + 1}"
            anchor = segment_anchors[idx]
            seg_level = segment_levels[idx] or 1
            level = max(1, min(split_level, seg_level))
            href = file_name
            if anchor:
                href = f"{file_name}#{anchor}"
            entry = TOCEntry(
                title=seg_title,
                href=href,
                file_href=file_name,
                anchor=anchor or "",
                depth=0,
            )
            while stack and stack[-1][0] >= level:
                stack.pop()
            if not stack:
                entry.depth = 0
                toc_entries.append(entry)
            else:
                parent_level, parent_entry = stack[-1]
                entry.depth = parent_entry.depth + 1
                parent_entry.children.append(entry)
            stack.append((level, entry))

    attach_chapter_indices_to_toc(toc_entries, anchor_map, max_depth=split_level)

    final_book = Book(
        metadata=metadata,
        spine=spine_chapters,
        toc=toc_entries,
        images={},
        source_file=os.path.basename(md_path),
        processed_at=datetime.now().isoformat(),
        anchor_map=anchor_map,
        split_level=split_level,
    )

    return final_book


def save_to_pickle(book: Book, output_dir: str):
    p_path = os.path.join(output_dir, 'book.pkl')
    with open(p_path, 'wb') as f:
        pickle.dump(book, f)
    print(f"Saved structured data to {p_path}")


# --- CLI ---

if __name__ == "__main__":

    import sys
    if len(sys.argv) < 2:
        print("Usage: python reader3.py <file.epub>")
        sys.exit(1)

    epub_file = sys.argv[1]
    assert os.path.exists(epub_file), "File not found."
    out_dir = os.path.splitext(epub_file)[0] + "_data"

    book_obj = process_epub(epub_file, out_dir)
    save_to_pickle(book_obj, out_dir)
    print("\n--- Summary ---")
    print(f"Title: {book_obj.metadata.title}")
    print(f"Authors: {', '.join(book_obj.metadata.authors)}")
    print(f"Physical Files (Spine): {len(book_obj.spine)}")
    print(f"TOC Root Items: {len(book_obj.toc)}")
    print(f"Images extracted: {len(book_obj.images)}")

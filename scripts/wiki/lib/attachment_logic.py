"""Pure attachment parsing helpers (testable without Confluence HTTP)."""

from __future__ import annotations

import csv
import io
import json
import os
import re
import urllib.parse
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

HANDLER_MAP_FILENAME = "confluence_attachment_handler_map.json"
HANDLER_MAP_EXAMPLE_FILENAME = "confluence_attachment_handler_map.example.json"
INVENTORY_DEFAULT_NAME = "attachment-type-inventory.json"

DEFAULT_EXTENSION_TO_HANDLER: Dict[str, str] = {
    ".txt": "text_plain",
    ".md": "text_plain",
    ".markdown": "text_plain",
    ".csv": "csv_utf8",
    ".tsv": "tsv_utf8",
    ".json": "json_text",
    ".xml": "text_plain",
    ".html": "text_plain",
    ".htm": "text_plain",
    ".log": "text_plain",
    ".yaml": "text_plain",
    ".yml": "text_plain",
    ".xlsx": "xlsx_openpyxl",
    ".pdf": "pdf_pypdf",
    ".png": "image_tesseract",
    ".jpg": "image_tesseract",
    ".jpeg": "image_tesseract",
    ".webp": "image_tesseract",
    ".gif": "image_tesseract",
    ".tif": "image_tesseract",
    ".tiff": "image_tesseract",
}


def safe_ext(filename: str) -> str:
    base = os.path.basename(filename)
    if "." not in base:
        return ""
    return "." + base.rsplit(".", 1)[-1].lower()


def user_handler_map_path(repo_root: Path) -> Path:
    return repo_root / "scripts" / "wiki" / HANDLER_MAP_FILENAME


def load_user_handler_map(repo_root: Path) -> Dict[str, str]:
    path = user_handler_map_path(repo_root)
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        out: Dict[str, str] = {}
        if isinstance(raw, dict):
            for key, value in raw.items():
                if isinstance(key, str) and isinstance(value, str):
                    normalized = key.lower().strip()
                    if not normalized.startswith("."):
                        normalized = "." + normalized
                    out[normalized] = value.strip()
        return out
    except Exception:
        return {}


def handler_text_plain(data: bytes) -> Tuple[str, str]:
    for enc in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return data.decode(enc), "ok"
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "ok(replace)"


def handler_csv_utf8(data: bytes) -> Tuple[str, str]:
    text, _ = handler_text_plain(data)
    buf = io.StringIO(text)
    try:
        rows = list(csv.reader(buf))
    except Exception as exc:
        return text[:8000], f"csv_fallback:{exc}"
    lines = []
    for row in rows[:500]:
        lines.append("\t".join(cell.replace("\n", " ") for cell in row))
    body = "\n".join(lines)
    if len(rows) > 500:
        body += f"\n… ({len(rows) - 500} more rows omitted)"
    return body, "ok"


def handler_tsv_utf8(data: bytes) -> Tuple[str, str]:
    text, _ = handler_text_plain(data)
    lines_out: List[str] = []
    for line in text.splitlines()[:2000]:
        lines_out.append(line.replace("\t", " | "))
    body = "\n".join(lines_out)
    if len(text.splitlines()) > 2000:
        body += "\n… (truncated)"
    return body, "ok"


def handler_json_text(data: bytes) -> Tuple[str, str]:
    text, _ = handler_text_plain(data)
    try:
        obj = json.loads(text)
        pretty = json.dumps(obj, ensure_ascii=False, indent=2)
        if len(pretty) > 120000:
            return pretty[:120000] + "\n… (truncated)", "ok_truncated"
        return pretty, "ok"
    except Exception:
        return text[:120000], "json_invalid_as_plain"


def handler_xlsx_openpyxl(data: bytes) -> Tuple[str, str]:
    try:
        import openpyxl  # type: ignore
    except ImportError:
        raise RuntimeError("missing_openpyxl")
    bio = io.BytesIO(data)
    workbook = openpyxl.load_workbook(bio, read_only=True, data_only=True)
    parts: List[str] = []
    max_rows_per_sheet = int(os.environ.get("CONFLUENCE_XLSX_MAX_ROWS", "400"))
    for sheet in workbook.worksheets[:15]:
        parts.append(f"### Sheet: {sheet.title}")
        row_count = 0
        for row in sheet.iter_rows(values_only=True):
            row_count += 1
            if row_count > max_rows_per_sheet:
                parts.append(f"… ({max_rows_per_sheet}+ rows omitted for this sheet)")
                break
            cells = []
            for cell in row:
                if cell is None:
                    cells.append("")
                else:
                    cells.append(str(cell).replace("\n", " "))
            if any(value.strip() for value in cells):
                parts.append("\t".join(cells))
        parts.append("")
    workbook.close()
    text = "\n".join(parts).strip()
    if len(text) > 200000:
        return text[:200000] + "\n… (truncated)", "ok_truncated"
    return text, "ok"


def handler_pdf_pypdf(data: bytes) -> Tuple[str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        raise RuntimeError("missing_pypdf")
    bio = io.BytesIO(data)
    reader = PdfReader(bio)
    max_pages = int(os.environ.get("CONFLUENCE_PDF_MAX_PAGES", "40"))
    chunks: List[str] = []
    for index, page in enumerate(reader.pages[:max_pages]):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        if page_text.strip():
            chunks.append(f"### Page {index + 1}\n{page_text.strip()}")
    body = "\n\n".join(chunks).strip()
    if not body:
        return "", "empty_pdf_text"
    if len(body) > 200000:
        return body[:200000] + "\n… (truncated)", "ok_truncated"
    return body, "ok"


def handler_image_tesseract(data: bytes) -> Tuple[str, str]:
    if os.environ.get("CONFLUENCE_IMAGE_OCR", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        raise RuntimeError("ocr_disabled")
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        raise RuntimeError("missing_pillow_or_pytesseract")

    bio = io.BytesIO(data)
    try:
        image = Image.open(bio)
    except Exception as exc:
        raise RuntimeError(f"bad_image:{exc}") from exc

    if getattr(image, "n_frames", 1) > 1:
        try:
            image.seek(0)
        except EOFError:
            pass

    max_px = int(os.environ.get("CONFLUENCE_OCR_MAX_PIXELS", "16000000"))
    width, height = image.size
    if width * height > max_px > 0:
        scale = (max_px / float(width * height)) ** 0.5
        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))
        try:
            resample = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
        except AttributeError:
            resample = Image.LANCZOS
        image = image.resize((new_width, new_height), resample)

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    lang = (os.environ.get("CONFLUENCE_OCR_LANG") or "chi_sim+eng").strip() or "chi_sim+eng"

    try:
        text = pytesseract.image_to_string(image, lang=lang)
    except Exception as exc:
        tnfe = getattr(pytesseract, "TesseractNotFoundError", None)
        if tnfe is not None and isinstance(exc, tnfe):
            raise RuntimeError("missing_tesseract_binary") from exc
        err = str(exc).lower()
        if "tesseract" in err and ("not installed" in err or "not found" in err):
            raise RuntimeError("missing_tesseract_binary") from exc
        raise RuntimeError(f"ocr_failed:{exc}") from exc

    text = (text or "").strip()
    if not text:
        return "", "empty_ocr"
    if len(text) > 80000:
        return text[:80000] + "\n… (truncated)", "ok_truncated"
    return text, "ok"


HANDLERS: Dict[str, Callable[[bytes], Tuple[str, str]]] = {
    "text_plain": handler_text_plain,
    "csv_utf8": handler_csv_utf8,
    "tsv_utf8": handler_tsv_utf8,
    "json_text": handler_json_text,
    "xlsx_openpyxl": handler_xlsx_openpyxl,
    "pdf_pypdf": handler_pdf_pypdf,
    "image_tesseract": handler_image_tesseract,
}


def resolve_handler_id(ext: str, user_map: Dict[str, str]) -> Optional[str]:
    normalized = ext.lower()
    if not normalized.startswith("."):
        normalized = "." + normalized
    if normalized in user_map:
        return user_map[normalized]
    return DEFAULT_EXTENSION_TO_HANDLER.get(normalized)


def extract_bytes(handler_id: str, data: bytes) -> Tuple[str, str, str]:
    hid = handler_id.strip().lower()
    if hid in ("", "skip", "none", "ignore"):
        return "", "skipped", "handler_skip"
    handler = HANDLERS.get(hid)
    if not handler:
        return "", "unsupported", f"unknown_handler:{hid}"
    try:
        text, note = handler(data)
        return text, "ok", note
    except RuntimeError as exc:
        msg = str(exc)
        if msg == "missing_openpyxl":
            return "", "unsupported", "install_openpyxl"
        if msg == "missing_pypdf":
            return "", "unsupported", "install_pypdf"
        if msg == "ocr_disabled":
            return "", "skipped", "CONFLUENCE_IMAGE_OCR=0"
        if msg == "missing_pillow_or_pytesseract":
            return "", "unsupported", "install_pillow_pytesseract_see_requirements-kb-attachments.txt"
        if msg == "missing_tesseract_binary":
            return (
                "",
                "unsupported",
                "install_tesseract_os_package_e_g_brew_install_tesseract_tesseract_lang",
            )
        if msg.startswith("bad_image:"):
            return "", "error", msg[:300]
        return "", "error", msg[:500]
    except Exception as exc:
        return "", "error", str(exc)[:500]


def discover_filenames_from_body_markup(
    view_html: str, storage_xml: str, page_id: str
) -> List[str]:
    raw = (view_html or "") + "\n" + (storage_xml or "")
    found: set[str] = set()
    pid = str(page_id).strip()

    for match in re.finditer(r'ri:filename=["\']([^"\']+)["\']', raw):
        token = (match.group(1) or "").strip()
        if token and "://" not in token and len(token) < 512:
            found.add(token)

    for match in re.finditer(
        r"/download/attachments/(\d+)/([^\s\"\'<>\?&]+)",
        raw,
        re.I,
    ):
        attachment_page_id, filename = match.group(1), match.group(2)
        filename = urllib.parse.unquote(filename.split("#")[0].split("?")[0]).strip()
        if attachment_page_id == pid and filename:
            found.add(filename)

    return sorted(found)


def attachment_download_url(wiki_base: str, page_id: str, att: Dict[str, Any]) -> str:
    links = att.get("_links") or {}
    download = (links.get("download") or "").strip()
    wiki_base = wiki_base.rstrip("/")
    parsed = urllib.parse.urlparse(wiki_base)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    if download.startswith("http"):
        return download
    if download.startswith("/"):
        if download.startswith("/wiki/"):
            return origin + download
        return origin + "/wiki" + download

    title = att.get("title") or "file"
    encoded = urllib.parse.quote(title)
    return f"{wiki_base}/download/attachments/{page_id}/{encoded}"


def merge_synthetic_attachments(
    meta_list: List[Dict[str, Any]], page_id: str, body_view: str, body_storage: str
) -> List[Dict[str, Any]]:
    titles = {(item.get("title") or "").strip() for item in meta_list}
    out = list(meta_list)
    for fname in discover_filenames_from_body_markup(body_view, body_storage, page_id):
        if fname not in titles:
            out.append(
                {
                    "title": fname,
                    "_links": {},
                    "metadata": {},
                    "extensions": {},
                }
            )
            titles.add(fname)
    return out

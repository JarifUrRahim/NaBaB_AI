"""Local file storage for uploads + artifacts.
For MVP: store on disk at /app/backend/uploads/{conv_id}/{file_id}__{filename}
Future: swap to S3-compatible / Emergent object storage.
"""
import re
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import UploadFile

UPLOAD_DIR = Path("/app/backend/uploads")
ARTIFACT_DIR = Path("/app/backend/artifacts")
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
ARTIFACT_DIR.mkdir(exist_ok=True, parents=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {
    "txt", "md", "json", "csv", "py", "js", "ts", "tsx", "jsx",
    "html", "css", "yaml", "yml", "xml", "log",
    "pdf", "doc", "docx",
    "jpg", "jpeg", "png", "gif", "webp", "svg", "bmp",
}


def _sanitize_filename(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._\- ]", "_", name)[:120]
    return safe or "file"


def _ext(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


async def save_upload(conv_id: str, upload: UploadFile) -> Dict[str, Any]:
    content = await upload.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large (max {MAX_FILE_SIZE // (1024*1024)} MB)")
    filename = _sanitize_filename(upload.filename or "file")
    if _ext(filename) not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed: .{_ext(filename)}")

    file_id = f"upl_{uuid.uuid4().hex[:12]}"
    conv_dir = UPLOAD_DIR / conv_id
    conv_dir.mkdir(exist_ok=True, parents=True)
    path = conv_dir / f"{file_id}__{filename}"
    path.write_bytes(content)
    return {
        "file_id": file_id,
        "filename": filename,
        "content_type": upload.content_type or "application/octet-stream",
        "size": len(content),
        "is_image": _ext(filename) in {"jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"},
    }


def find_file(conv_id: str, file_id: str, kind: str = "any") -> Optional[Path]:
    bases = []
    if kind in ("any", "upload"):
        bases.append(UPLOAD_DIR / conv_id)
    if kind in ("any", "artifact"):
        bases.append(ARTIFACT_DIR / conv_id)
    for base in bases:
        if not base.exists():
            continue
        for p in base.iterdir():
            if p.name.startswith(file_id + "__"):
                return p
    return None

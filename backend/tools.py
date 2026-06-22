"""NaBaB Agent Tools — Phase B
Built-in tool definitions and executors. Uses Emergent LLM tool-calling.
All tools return JSON-stringifiable dict (always wrapped in a result envelope).
"""
import os
import subprocess
import asyncio
import re
import uuid
from pathlib import Path
from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup

ARTIFACT_DIR = Path("/app/backend/artifacts")
UPLOAD_DIR = Path("/app/backend/uploads")
ARTIFACT_DIR.mkdir(exist_ok=True, parents=True)
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

MAX_OUTPUT = 8000  # cap returned content size per tool call


# ---------- Tool Schemas (OpenAI-style function spec) ----------
TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web (DuckDuckGo) for current information. Returns top results with title, snippet, and URL. Use when you need recent or external info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "limit": {"type": "integer", "description": "Number of results (1-10, default 5)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_url",
            "description": "Fetch and extract clean text content from a web URL. Use for reading specific articles, docs, or pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full URL (must start with http/https)"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Save a file as a permanent artifact in this conversation. Use for generating code, documents, or any output the user should be able to download. Returns the file_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename with extension (e.g. 'index.html', 'app.py', 'report.md')",
                    },
                    "content": {"type": "string", "description": "Full file content as text"},
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read an uploaded file's text content by file_id. Use to inspect files the user has attached.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "The file_id from upload"},
                },
                "required": ["file_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files (uploaded + artifacts) in this conversation.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute Python code in a sandboxed subprocess (10s timeout, no network). Use for calculations, data processing, plotting (saves PNG to artifacts), or testing logic. Returns stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Complete Python code to execute"},
                },
                "required": ["code"],
            },
        },
    },
]


# ---------- Tool Executors ----------
async def _web_search(query: str, limit: int = 5) -> Dict[str, Any]:
    try:
        from duckduckgo_search import DDGS
        limit = max(1, min(int(limit or 5), 10))
        # DDGS is synchronous; run in thread
        def _run():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=limit))
        results = await asyncio.to_thread(_run)
        return {
            "ok": True,
            "query": query,
            "results": [
                {"title": r.get("title", ""), "snippet": r.get("body", "")[:400], "url": r.get("href", "")}
                for r in results
            ],
        }
    except Exception as e:
        return {"ok": False, "error": f"web_search failed: {str(e)[:300]}"}


async def _read_url(url: str) -> Dict[str, Any]:
    if not re.match(r"^https?://", url):
        return {"ok": False, "error": "URL must start with http:// or https://"}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers={"User-Agent": "NaBaB-Agent/1.0"}) as cli:
            r = await cli.get(url)
        if r.status_code >= 400:
            return {"ok": False, "error": f"HTTP {r.status_code}"}
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        text = re.sub(r"\s+\n", "\n", soup.get_text(separator="\n").strip())
        text = re.sub(r"\n{3,}", "\n\n", text)
        if len(text) > MAX_OUTPUT:
            text = text[:MAX_OUTPUT] + "\n\n[...truncated...]"
        return {"ok": True, "url": url, "title": title, "content": text}
    except Exception as e:
        return {"ok": False, "error": f"read_url failed: {str(e)[:300]}"}


async def _write_file(conv_id: str, filename: str, content: str) -> Dict[str, Any]:
    # Sanitize filename
    safe = re.sub(r"[^a-zA-Z0-9._\- ]", "_", filename)[:120]
    if not safe:
        safe = "file.txt"
    file_id = f"art_{uuid.uuid4().hex[:12]}"
    conv_dir = ARTIFACT_DIR / conv_id
    conv_dir.mkdir(exist_ok=True, parents=True)
    path = conv_dir / f"{file_id}__{safe}"
    try:
        path.write_text(content, encoding="utf-8")
        return {
            "ok": True,
            "file_id": file_id,
            "filename": safe,
            "size": len(content.encode("utf-8")),
            "download_url": f"/api/files/artifact/{conv_id}/{file_id}",
        }
    except Exception as e:
        return {"ok": False, "error": f"write_file failed: {str(e)[:300]}"}


async def _read_file(conv_id: str, file_id: str) -> Dict[str, Any]:
    # Search uploads first, then artifacts
    for base in [UPLOAD_DIR / conv_id, ARTIFACT_DIR / conv_id]:
        if not base.exists():
            continue
        for p in base.iterdir():
            if p.name.startswith(file_id + "__") or p.name == file_id:
                try:
                    data = p.read_text(encoding="utf-8", errors="replace")
                    if len(data) > MAX_OUTPUT:
                        data = data[:MAX_OUTPUT] + "\n[...truncated...]"
                    return {"ok": True, "file_id": file_id, "filename": p.name.split("__", 1)[-1], "content": data}
                except Exception as e:
                    return {"ok": False, "error": f"read_file failed: {e}"}
    return {"ok": False, "error": f"file_id '{file_id}' not found in this conversation"}


async def _list_files(conv_id: str) -> Dict[str, Any]:
    items = []
    for kind, base in [("upload", UPLOAD_DIR / conv_id), ("artifact", ARTIFACT_DIR / conv_id)]:
        if not base.exists():
            continue
        for p in base.iterdir():
            if not p.is_file():
                continue
            parts = p.name.split("__", 1)
            if len(parts) == 2:
                fid, fname = parts
            else:
                fid, fname = p.stem, p.name
            items.append({"file_id": fid, "filename": fname, "kind": kind, "size": p.stat().st_size})
    return {"ok": True, "files": items}


async def _execute_python(code: str) -> Dict[str, Any]:
    """Sandboxed subprocess Python exec — restricted environment."""
    if len(code) > 20000:
        return {"ok": False, "error": "Code too large (max 20k chars)"}
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
        except asyncio.TimeoutError:
            proc.kill()
            return {"ok": False, "error": "Execution timed out (10s limit)"}
        out = stdout.decode("utf-8", errors="replace")[:MAX_OUTPUT]
        err = stderr.decode("utf-8", errors="replace")[:MAX_OUTPUT]
        return {
            "ok": proc.returncode == 0,
            "stdout": out,
            "stderr": err,
            "exit_code": proc.returncode,
        }
    except Exception as e:
        return {"ok": False, "error": f"execution error: {str(e)[:300]}"}


# ---------- Dispatcher ----------
async def execute_tool(name: str, args: Dict[str, Any], conv_id: str) -> Dict[str, Any]:
    try:
        if name == "web_search":
            return await _web_search(args.get("query", ""), args.get("limit", 5))
        if name == "read_url":
            return await _read_url(args.get("url", ""))
        if name == "write_file":
            return await _write_file(conv_id, args.get("filename", "file.txt"), args.get("content", ""))
        if name == "read_file":
            return await _read_file(conv_id, args.get("file_id", ""))
        if name == "list_files":
            return await _list_files(conv_id)
        if name == "execute_python":
            return await _execute_python(args.get("code", ""))
        return {"ok": False, "error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"ok": False, "error": f"tool dispatcher error: {str(e)[:300]}"}


# ---------- Credit cost per tool ----------
TOOL_CREDIT_COST = {
    "web_search": 5,
    "read_url": 3,
    "read_file": 2,
    "list_files": 1,
    "write_file": 4,
    "execute_python": 10,
}
DEFAULT_TOOL_COST = 5

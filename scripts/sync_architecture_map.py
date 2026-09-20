#!/usr/bin/env python3
"""根据 docs/ai/module-map.yaml 校验路径并重写 architecture-map.md。"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAP_YAML = ROOT / "docs/ai/module-map.yaml"
MAP_MD = ROOT / "docs/ai/architecture-map.md"
DOCS_INDEX = ROOT / "docs/README.md"


def _docs_md_not_in_index() -> list[str]:
    """每个 docs/**/*.md 必须在 docs/README.md 里出现相对路径链接。"""
    index = DOCS_INDEX.read_text(encoding="utf-8")
    docs_root = ROOT / "docs"
    missing: list[str] = []
    for path in sorted(docs_root.rglob("*.md")):
        if path == DOCS_INDEX:
            continue
        rel = path.relative_to(docs_root).as_posix()
        if f"]({rel})" not in index:
            missing.append(rel)
    return missing


def main() -> int:
    data = yaml.safe_load(MAP_YAML.read_text(encoding="utf-8"))
    modules = data.get("modules") or []
    missing = []
    rows = []
    for item in modules:
        path = item["path"]
        full = ROOT / path
        if not full.exists():
            missing.append(path)
        rows.append(
            f"| `{path}` | {item.get('role', '')} | {item.get('owner', '')} | "
            f"{item.get('purpose', '')} | {item.get('forbidden', '')} |"
        )
    body = "\n".join(
        [
            "# 目录实况（自动生成）",
            "",
            "勿手改本文件。源文件是 [`module-map.yaml`](module-map.yaml)。",
            "改目录职责后执行：`python scripts/sync_architecture_map.py`。",
            "",
            "架构对错仍以 [system-design.md](../architecture/system-design.md) 为准。",
            "",
            "| 路径 | 角色 | 维护方 | 职责 | 禁止 |",
            "|------|------|--------|------|------|",
            *rows,
            "",
            "## 给 AI 的阅读顺序",
            "",
            "1. `AGENTS.md`；按需打开 [docs/README.md](../README.md)",
            "2. 本表定位目录",
            "3. `docs/ai/memory.md` 看已拍板例外",
            "4. 对应代码",
            "",
        ]
    )
    MAP_MD.write_text(body, encoding="utf-8")
    unindexed = _docs_md_not_in_index()
    if missing:
        print("missing module-map paths:")
        for p in missing:
            print(" -", p)
    if unindexed:
        print("docs not linked from docs/README.md:")
        for p in unindexed:
            print(" -", p)
    if missing or unindexed:
        return 1
    print(f"wrote {MAP_MD.relative_to(ROOT)} ({len(modules)} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

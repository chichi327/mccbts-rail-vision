#!/usr/bin/env python3
"""根据 docs/ai/module-map.yaml 校验路径并重写 architecture-map.md。"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAP_YAML = ROOT / "docs/ai/module-map.yaml"
MAP_MD = ROOT / "docs/ai/architecture-map.md"


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
            "1. `AGENTS.md`",
            "2. 本表定位目录",
            "3. `docs/ai/memory.md` 看已拍板例外",
            "4. 对应代码",
            "",
        ]
    )
    MAP_MD.write_text(body, encoding="utf-8")
    if missing:
        print("missing paths:")
        for p in missing:
            print(" -", p)
        return 1
    print(f"wrote {MAP_MD.relative_to(ROOT)} ({len(modules)} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

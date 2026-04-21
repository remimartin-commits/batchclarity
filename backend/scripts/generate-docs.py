from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
APP_ROOT = BACKEND_ROOT / "app"
OUTPUT_ROOT = REPO_ROOT / "docs" / "generated"
SITE_ROOT = REPO_ROOT / "docs" / "site"


def _py_files(path: Path) -> list[Path]:
    return [p for p in path.rglob("*.py") if ".venv" not in p.parts and "__pycache__" not in p.parts]


def generate_openapi() -> dict[str, Any]:
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "GMP Platform API",
            "version": "0.1.0",
            "description": "Static CI-safe OpenAPI placeholder. Run app runtime for full schema.",
        },
        "paths": {},
    }
    (OUTPUT_ROOT / "openapi.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return schema


def _module_from_file(path: Path) -> str:
    parts = path.relative_to(APP_ROOT).parts
    if len(parts) >= 3 and parts[0] == "modules":
        return parts[1]
    if len(parts) >= 2 and parts[0] == "core":
        return f"core.{parts[1]}"
    return "app"


def generate_module_dependency_graph() -> str:
    module_files = _py_files(APP_ROOT / "modules")
    edges: set[tuple[str, str, str]] = set()

    for file_path in module_files:
        source = _module_from_file(file_path)
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.modules."):
                target = node.module.split(".")[2]
                if target != source:
                    edges.add((source, target, "import"))

    graph = ["graph LR"]
    if not edges:
        graph.append("  modules[\"No cross-module imports detected\"]")
    else:
        for source, target, kind in sorted(edges):
            graph.append(f"  {source} -->|{kind}| {target}")

    mermaid = "\n".join(graph)
    md = [
        "# Module Dependency Graph",
        "",
        "Auto-generated from Python imports across `backend/app/modules`.",
        "",
        "```mermaid",
        mermaid,
        "```",
        "",
    ]
    output = "\n".join(md)
    (OUTPUT_ROOT / "module-dependency-graph.md").write_text(output, encoding="utf-8")
    return mermaid


def generate_event_catalog() -> dict[str, Any]:
    events: dict[str, dict[str, Any]] = {}
    for file_path in _py_files(APP_ROOT):
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        rel = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr != "send_event":
                    continue
                event_name = None
                for kw in node.keywords:
                    if kw.arg == "event_type" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        event_name = kw.value.value
                if not event_name:
                    continue
                row = events.setdefault(
                    event_name,
                    {"event_type": event_name, "schema": "context: dict", "producers": set(), "consumers": set()},
                )
                row["producers"].add(rel)

    for event in events.values():
        event["producers"] = sorted(event["producers"])
        event["consumers"] = sorted(event["consumers"])

    payload = {"events": [events[k] for k in sorted(events)]}
    (OUTPUT_ROOT / "event-catalog.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# Event Catalog", "", "Auto-generated from `send_event(...)` call sites.", ""]
    if not payload["events"]:
        lines.append("No events found.")
    else:
        for event in payload["events"]:
            lines.extend(
                [
                    f"## {event['event_type']}",
                    f"- Schema: `{event['schema']}`",
                    "- Producers:",
                    *[f"  - `{p}`" for p in event["producers"]],
                    "- Consumers:",
                    *(["  - _none declared in-code_"] if not event["consumers"] else [f"  - `{c}`" for c in event["consumers"]]),
                    "",
                ]
            )
    (OUTPUT_ROOT / "event-catalog.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def generate_schema_per_module() -> dict[str, list[str]]:
    by_module: dict[str, list[str]] = defaultdict(list)
    table_marker = "__tablename__ ="
    for file_path in _py_files(APP_ROOT):
        module = _module_from_file(file_path)
        text = file_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith(table_marker):
                continue
            if '"' in stripped:
                table = stripped.split('"')[1]
                by_module[module].append(table)
            elif "'" in stripped:
                table = stripped.split("'")[1]
                by_module[module].append(table)

    lines = [
        "# Database Schema by Module",
        "",
        "Auto-generated from model file table declarations.",
        "",
    ]
    for module in sorted(by_module):
        lines.append(f"## {module}")
        for table_name in sorted(by_module[module]):
            lines.append(f"- `{table_name}`")
        lines.append("")

    (OUTPUT_ROOT / "database-schema-by-module.md").write_text("\n".join(lines), encoding="utf-8")
    return {k: sorted(v) for k, v in sorted(by_module.items())}


def _write_site(openapi_schema: dict[str, Any], module_graph: str, event_catalog: dict[str, Any], schema: dict[str, list[str]]) -> None:
    SITE_ROOT.mkdir(parents=True, exist_ok=True)
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>GMP Platform Generated Docs</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; line-height: 1.4; }}
    pre {{ background: #f3f3f3; padding: 1rem; overflow: auto; }}
    code {{ background: #f3f3f3; padding: 0.1rem 0.3rem; }}
  </style>
</head>
<body>
  <h1>GMP Platform Generated Docs</h1>
  <ul>
    <li><a href="../generated/openapi.json">OpenAPI JSON</a></li>
    <li><a href="../generated/module-dependency-graph.md">Module dependency graph (Markdown)</a></li>
    <li><a href="../generated/event-catalog.md">Event catalog (Markdown)</a></li>
    <li><a href="../generated/database-schema-by-module.md">Database schema by module (Markdown)</a></li>
  </ul>
  <h2>API Summary</h2>
  <p>Path count: <strong>{len(openapi_schema.get("paths", {}))}</strong></p>
  <h2>Module Dependency Graph (Mermaid source)</h2>
  <pre>{module_graph}</pre>
  <h2>Event Count</h2>
  <p><strong>{len(event_catalog.get("events", []))}</strong></p>
  <h2>Modules With Tables</h2>
  <pre>{json.dumps(schema, indent=2)}</pre>
</body>
</html>
"""
    (SITE_ROOT / "index.html").write_text(html, encoding="utf-8")
    (SITE_ROOT / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    openapi_schema = generate_openapi()
    module_graph = generate_module_dependency_graph()
    event_catalog = generate_event_catalog()
    schema = generate_schema_per_module()
    _write_site(openapi_schema, module_graph, event_catalog, schema)
    print("Generated docs in docs/generated and docs/site.")


if __name__ == "__main__":
    main()

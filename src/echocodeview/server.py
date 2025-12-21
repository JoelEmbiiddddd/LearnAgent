import os
import posixpath
from dataclasses import dataclass

from flask import Flask, redirect, render_template, url_for
from markdown import Markdown
from werkzeug.serving import make_server

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 3000
EXCLUDED_DIRS = {
    ".git",
    ".codex",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "server",
}


@dataclass(frozen=True)
class ServerConfig:
    root_dir: str
    entry_rel: str
    host: str
    port: int


def is_markdown_file(name):
    return name.lower().endswith(".md")


def extract_title(markdown_text):
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return None


def build_tree(root_dir):
    def walk_dir(current_dir, rel_prefix):
        try:
            entries = sorted(os.listdir(current_dir), key=str.lower)
        except OSError:
            return []

        directories = []
        files = []

        for entry in entries:
            if entry.startswith(".") or entry.lower() in EXCLUDED_DIRS:
                continue
            abs_path = os.path.join(current_dir, entry)
            rel_path = posixpath.join(rel_prefix, entry) if rel_prefix else entry
            if os.path.isdir(abs_path):
                directories.append((entry, abs_path, rel_path))
            elif is_markdown_file(entry):
                files.append((entry, abs_path, rel_path))

        nodes = []

        for entry, abs_path, rel_path in directories:
            children = walk_dir(abs_path, rel_path)
            if children:
                nodes.append(
                    {
                        "type": "dir",
                        "name": entry,
                        "path": rel_path,
                        "children": children,
                    }
                )

        for entry, abs_path, rel_path in files:
            title = entry
            nodes.append(
                {
                    "type": "file",
                    "name": entry,
                    "path": rel_path,
                    "title": title,
                }
            )

        return nodes

    return walk_dir(root_dir, "")


def mark_active(tree, active_rel):
    marked = []
    for node in tree:
        if node["type"] == "dir":
            children = mark_active(node["children"], active_rel)
            has_active = any(child.get("active") or child.get("open") for child in children)
            marked.append(
                {
                    **node,
                    "children": children,
                    "open": has_active,
                }
            )
        else:
            marked.append(
                {
                    **node,
                    "active": node["path"] == active_rel,
                }
            )
    return marked


def find_first_file(tree):
    for node in tree:
        if node["type"] == "file":
            return node["path"]
        if node["type"] == "dir":
            found = find_first_file(node["children"])
            if found:
                return found
    return None


def find_default_entry(root_dir, tree):
    for entry in os.listdir(root_dir):
        if is_markdown_file(entry) and entry.lower() == "readme.md":
            return entry
    return find_first_file(tree)


def resolve_file_path(root_dir, rel_path):
    normalized = rel_path.replace("\\", "/")
    candidate = os.path.abspath(os.path.join(root_dir, normalized))
    root_abs = os.path.abspath(root_dir)
    if os.path.commonpath([root_abs, candidate]) != root_abs:
        return None
    return candidate


def inject_toc_marker(markdown_text):
    if "[TOC]" in markdown_text:
        return markdown_text
    lines = markdown_text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("#"):
            lines.insert(index, "[TOC]")
            lines.insert(index + 1, "")
            return "\n".join(lines)
    return "[TOC]\n\n" + markdown_text


def inject_mermaid_blocks(markdown_text):
    lines = markdown_text.splitlines()
    output = []
    mermaid_lines = []
    in_mermaid = False

    for line in lines:
        stripped = line.strip()
        if not in_mermaid and stripped.startswith("```mermaid"):
            in_mermaid = True
            mermaid_lines = []
            continue

        if in_mermaid:
            if stripped.startswith("```"):
                output.append('<div class="mermaid">')
                output.extend(mermaid_lines)
                output.append("</div>")
                in_mermaid = False
            else:
                mermaid_lines.append(line)
            continue

        output.append(line)

    if in_mermaid:
        output.append("```mermaid")
        output.extend(mermaid_lines)

    return "\n".join(output)


def create_renderer():
    return Markdown(
        extensions=["toc", "tables", "fenced_code", "codehilite"],
        extension_configs={
            "toc": {
                "permalink": "#",
                "permalink_class": "headerlink",
                "toc_depth": "2-6",
            }
        },
        output_format="html5",
    )


def render_markdown(markdown_text):
    renderer = create_renderer()
    return renderer.convert(markdown_text)


def resolve_config(root_dir, entry_path, host, port):
    if not root_dir:
        root_dir = os.getcwd()

    root_dir = os.path.abspath(root_dir)
    if not os.path.isdir(root_dir):
        raise ValueError(f"Root directory not found: {root_dir}")

    tree = build_tree(root_dir)
    if not tree:
        raise ValueError("No markdown files found under root directory.")

    if entry_path:
        entry_path = os.path.abspath(entry_path)
        if not os.path.exists(entry_path):
            raise ValueError(f"Entry file not found: {entry_path}")
        if not is_markdown_file(os.path.basename(entry_path)):
            raise ValueError("Entry file must be a markdown file.")
        entry_rel = os.path.relpath(entry_path, root_dir).replace("\\", "/")
        if entry_rel.startswith(".."):
            raise ValueError("Entry file must be inside root directory.")
    else:
        entry_rel = find_default_entry(root_dir, tree)

    if not entry_rel:
        raise ValueError("No markdown entry resolved.")

    return ServerConfig(
        root_dir=root_dir,
        entry_rel=entry_rel,
        host=host or DEFAULT_HOST,
        port=port or DEFAULT_PORT,
    )


def create_app(root_dir, entry_rel):
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    @app.route("/")
    def index():
        tree = build_tree(root_dir)
        if not tree:
            return render_template("error.html", message="No markdown files found.")
        default_rel = entry_rel or find_default_entry(root_dir, tree)
        return redirect(url_for("view_file", relpath=default_rel))

    @app.route("/view/<path:relpath>")
    def view_file(relpath):
        tree = build_tree(root_dir)
        if not tree:
            return render_template("error.html", message="No markdown files found.")

        resolved = resolve_file_path(root_dir, relpath)
        if not resolved or not os.path.exists(resolved):
            return render_template("error.html", message=f"File not found: {relpath}")

        with open(resolved, "r", encoding="utf-8") as handle:
            markdown_text = inject_toc_marker(handle.read())
            markdown_text = inject_mermaid_blocks(markdown_text)

        html = render_markdown(markdown_text)
        title = extract_title(markdown_text) or os.path.basename(relpath)
        marked_tree = mark_active(tree, relpath)

        return render_template(
            "doc.html",
            markdown_html=html,
            file_tree=marked_tree,
            root_dir=root_dir,
            active_rel=relpath,
            title=title,
        )

    return app


def start_document_web_server(root_dir, entry_path=None, host=None, port=None, open_browser=True):
    config = resolve_config(root_dir, entry_path, host, port)
    app = create_app(config.root_dir, config.entry_rel)
    server = make_server(config.host, config.port, app)
    actual_port = server.server_port
    url = f"http://{config.host}:{actual_port}/"

    print("echocodeview server started")
    print(f"Root: {config.root_dir}")
    print(f"Entry: {config.entry_rel}")
    print(f"URL: {url}")

    if open_browser:
        import webbrowser

        webbrowser.open(url)

    server.serve_forever()

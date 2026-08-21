import pathlib

import nbformat

from . import __version__
from .deps import resolve_dependencies
from .notebook import assemble_notebook, content_hash, make_markdown_cell, make_pip_cell, make_writefile_cell
from .state import STATE_DIR, ensure_gitignore_entries, save_manifest
from .targets import get_target
from .traversal import traverse
from .warnings import get_warning_cells


def _is_binary(file_path: pathlib.Path, include: set = None) -> bool:
    binary_extensions = {
        '.pkl', '.pt', '.h5', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz',
        '.csv', '.tsv', '.xlsx', '.xls', '.parquet', '.db', '.sqlite', '.pdf', '.ipynb',
    }
    if include:
        include_exts = {ext.lower() if ext.startswith('.') else '.' + ext.lower() for ext in include}
        binary_extensions = binary_extensions - include_exts
    return file_path.suffix.lower() in binary_extensions


SETUP_HEADER = "## 🔧 repo2nb setup (safe to collapse)\n\nGit auth and dependency installation. Collapsed where the viewer supports it — expand if you need to debug."


def convert(repo_path: pathlib.Path, output_path: pathlib.Path, omit_instructions: bool = False,
            ignore_extra: set = None, include: set = None, target_name: str = "kaggle",
            deps: bool = True):
    target = get_target(target_name)
    ignore_extra = ignore_extra or set()

    # State files must exist before traversal so hashes are stable across runs.
    ensure_gitignore_entries(repo_path, [*target.GITIGNORE_ENTRIES, f"{STATE_DIR}/"])

    tree, has_git = traverse(repo_path, extra_ignore=ignore_extra)

    cells = []

    if not omit_instructions:
        cells.extend(get_warning_cells())

    setup_cells = []
    push_cells = []
    if has_git:
        setup_cells.extend(target.auth_cells(repo_path, omit_instructions))
        push_cells = target.workspace_cells(omit_instructions)

    file_hashes = {}
    if deps:
        requirements, source = resolve_dependencies(repo_path, tree)
        if requirements:
            setup_cells.append(make_pip_cell(requirements))
            print(f"[repo2nb] Dependencies resolved from {source}: {len(requirements)} package(s)")
        elif source.startswith(("poetry", "uv", "requirements")):
            print(f"[repo2nb] WARNING: dependency source '{source}' produced no installable requirements.")

    if setup_cells:
        cells.append(make_markdown_cell(SETUP_HEADER))
        collapse = target.collapse_metadata()
        for cell in setup_cells:
            # Collapse code cells only; keep instruction markdown readable for debugging.
            if cell.cell_type == "code":
                cell.metadata.update(collapse)
            cells.append(cell)

    if omit_instructions:
        phase2_text = "# 📂 Phase 2: Repository Construction"
    else:
        phase2_text = (
            "# 📂 Phase 2: Repository Construction\n"
            "---\n"
            "The following cells will recreate your project files within Kaggle's environment."
        )
    cells.append(make_markdown_cell(phase2_text))

    repo_name = repo_path.name

    for dir_path, files in tree:
        if not files:
            continue

        if dir_path == repo_path:
            depth = 0
            folder_name = repo_name
        else:
            try:
                rel_dir = dir_path.relative_to(repo_path)
                depth = len(rel_dir.parts)
            except ValueError:
                depth = 0
            folder_name = dir_path.name

        if depth == 0:
            header_level = "#"
        elif depth == 1:
            header_level = "##"
        elif depth == 2:
            header_level = "###"
        else:
            header_level = "####"

        cells.append(make_markdown_cell(f"{header_level} 📁 {folder_name}"))

        for file_path in files:
            try:
                rel_file_path = file_path.relative_to(repo_path)
            except ValueError:
                continue

            kag_path = rel_file_path.as_posix()

            if _is_binary(file_path, include):
                cells.append(make_markdown_cell(f"**Skipped data/binary file**: `{kag_path}`\n*(Upload manually if needed)*"))
                continue

            cells.append(make_markdown_cell(f"**📄 {rel_file_path.name}**"))
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                cells.append(make_writefile_cell(kag_path, content, prefix=target.WORKDIR_PREFIX))
                file_hashes[kag_path] = content_hash(content)
            except UnicodeDecodeError:
                cells.append(make_markdown_cell(f"**Skipped non-UTF8 file**: `{kag_path}`\n*(Upload manually if needed)*"))

    cells.extend(push_cells)

    nb = assemble_notebook(cells, target=target_name)

    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    manifest = {
        "version": __version__,
        "generated_at": nb.metadata["repo2nb"]["generated_at"],
        "target": target_name,
        "notebook": str(output_path),
        "ignore_extra": sorted(ignore_extra),
        "files": file_hashes,
    }
    save_manifest(repo_path, manifest)

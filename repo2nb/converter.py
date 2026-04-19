import pathlib
import nbformat
from .traversal import traverse
from .warnings import get_warning_cells
from .git import get_git_cells
from .notebook import make_markdown_cell, make_writefile_cell, assemble_notebook

def _is_binary(file_path: pathlib.Path, include: set = None) -> bool:
    binary_extensions = {
        '.pkl', '.pt', '.h5', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz',
        '.csv', '.tsv', '.xlsx', '.xls', '.parquet', '.db', '.sqlite', '.pdf', '.ipynb', 
    }
    if include:
        include_exts = {ext.lower() if ext.startswith('.') else '.' + ext.lower() for ext in include}
        binary_extensions = binary_extensions - include_exts
    return file_path.suffix.lower() in binary_extensions

def convert(repo_path: pathlib.Path, output_path: pathlib.Path, omit_instructions: bool = False, ignore_extra: set = None, include: set = None):
    ignore_extra = ignore_extra or set()
    ignore_exts = {ext.lower() if ext.startswith('.') else '.' + ext.lower() for ext in ignore_extra}
    
    tree, has_git = traverse(repo_path)
    
    cells = []
    
    if not omit_instructions:
        cells.extend(get_warning_cells())
    
    if has_git:
        setup_cells, push_cells = get_git_cells(repo_path, omit_instructions)
        cells.extend(setup_cells)
        
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
        valid_files = [f for f in files if f.suffix.lower() not in ignore_exts]
        if not valid_files:
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
        
        for file_path in valid_files:
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
                cells.append(make_writefile_cell(kag_path, content))
            except UnicodeDecodeError:
                cells.append(make_markdown_cell(f"**Skipped non-UTF8 file**: `{kag_path}`\n*(Upload manually if needed)*"))
                
    if has_git:
        cells.extend(push_cells)
        
    nb = assemble_notebook(cells)
    
    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

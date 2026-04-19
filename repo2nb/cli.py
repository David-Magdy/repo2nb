import click
import pathlib
from .converter import convert

@click.command()
@click.argument("repo_path", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path))
@click.option("--output", "-o", type=click.Path(dir_okay=False, path_type=pathlib.Path), help="Output .ipynb path")
@click.option("--omit-instructions", is_flag=True, default=False, help="Omit warning cells and instructional cheat sheets.")
@click.option("--ignore-extra", type=str, help="Extra file extensions to ignore completely (e.g. '.mp4 .yaml').")
@click.option("--include", type=str, help="File extensions to force include (e.g. '.csv .json').")
def main(repo_path, output, omit_instructions, ignore_extra, include):
    """Convert a local directory into a reproducible Jupyter Notebook for Kaggle."""
    if not output:
        output = pathlib.Path(f"{repo_path.name}.ipynb")
    
    ignore_set = set(ignore_extra.replace(",", " ").split()) if ignore_extra else set()
    include_set = set(include.replace(",", " ").split()) if include else set()
    
    convert(repo_path, output, omit_instructions, ignore_set, include_set)

if __name__ == "__main__":
    main()

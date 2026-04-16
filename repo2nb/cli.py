import click
import pathlib
from .converter import convert

@click.command()
@click.argument("repo_path", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path))
@click.option("--output", "-o", type=click.Path(dir_okay=False, path_type=pathlib.Path), help="Output .ipynb path")
@click.option("--omit-instructions", is_flag=True, default=False, help="Omit warning cells and instructional cheat sheets.")
def main(repo_path, output, omit_instructions):
    """Convert a local directory into a reproducible Jupyter Notebook for Kaggle."""
    if not output:
        output = pathlib.Path(f"{repo_path.name}.ipynb")
    
    convert(repo_path, output, omit_instructions)

if __name__ == "__main__":
    main()

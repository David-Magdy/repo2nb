import argparse
import pathlib
import sys

from . import __version__
from .converter import convert
from .reverse import reverse
from .sync import sync


def _convert_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo2nb",
        description="Convert a local repository into a reproducible Jupyter Notebook for Kaggle/Colab.",
    )
    parser.add_argument("--version", action="version", version=f"repo2nb {__version__}")
    parser.add_argument("repo_path", nargs="?", type=pathlib.Path,
                        help="Repository directory to convert.")
    parser.add_argument("--output", "-o", type=pathlib.Path, help="Output .ipynb path")
    parser.add_argument("--target", choices=["kaggle", "colab"], default="kaggle",
                        help="Target platform (default: kaggle)")
    parser.add_argument("--omit-instructions", action="store_true",
                        help="Omit warning cells and instructional cheat sheets.")
    parser.add_argument("--ignore-extra", type=str,
                        help="Extra file extensions to ignore completely (e.g. '.mp4 .yaml').")
    parser.add_argument("--include", type=str,
                        help="File extensions to force include (e.g. '.csv .json').")
    parser.add_argument("--no-deps", action="store_true",
                        help="Skip dependency auto-detection and the pip install cell.")
    return parser


def _reverse_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo2nb reverse",
        description="Extract files from a repo2nb-generated notebook back into a directory (nb2repo).",
    )
    parser.add_argument("notebook_path", type=pathlib.Path, help="Notebook to extract files from.")
    parser.add_argument("--output", "-o", type=pathlib.Path,
                        help="Output directory (default: <notebook name> without extension).")
    parser.add_argument("--force", action="store_true",
                        help="Allow writing into a non-empty output directory.")
    return parser


def _sync_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo2nb sync",
        description="One-directional incremental sync (repo -> notebook). Edits made on Kaggle are "
                    "NOT merged back; run 'repo2nb reverse' first to bring them into your repo.",
    )
    parser.add_argument("repo_path", type=pathlib.Path, help="Repository directory.")
    parser.add_argument("--notebook", type=pathlib.Path,
                        help="Target notebook path (default: path recorded at last generation).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without touching anything.")
    return parser


def _split_extensions(value: str) -> set:
    return set(value.replace(",", " ").split()) if value else set()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    # Manual dispatch instead of argparse subparsers: an optional leading positional
    # (repo_path) can't coexist with subparsers in one parser. Gotcha: a local folder
    # literally named 'sync'/'reverse' is treated as the subcommand — use './sync'.
    command = argv[0] if argv else None

    if command == "reverse":
        args = _reverse_parser().parse_args(argv[1:])
        output = args.output or pathlib.Path(args.notebook_path.stem)
        reverse(args.notebook_path, output, force=args.force)
    elif command == "sync":
        args = _sync_parser().parse_args(argv[1:])
        sync(args.repo_path, notebook_path=args.notebook, dry_run=args.dry_run)
    else:
        args = _convert_parser().parse_args(argv)
        if not args.repo_path:
            _convert_parser().error("the following arguments are required: repo_path")
        if not args.repo_path.is_dir():
            sys.exit(f"[repo2nb] Repository path '{args.repo_path}' does not exist or is not a directory.")
        output = args.output or pathlib.Path(f"{args.repo_path.name}.ipynb")
        convert(
            args.repo_path,
            output,
            omit_instructions=args.omit_instructions,
            ignore_extra=_split_extensions(args.ignore_extra),
            include=_split_extensions(args.include),
            target_name=args.target,
            deps=not args.no_deps,
        )


if __name__ == "__main__":
    main()

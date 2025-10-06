#!/usr/bin/env python
"""CLI entrypoint for Agentic Connector Builder WebApp."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Run the Agentic Connector Builder WebApp using Reflex.

    This entrypoint allows running the app with uvx or as an installed command.
    It locates the app directory (containing rxconfig.py) and runs reflex from there.
    """
    package_dir = Path(__file__).parent

    if (package_dir / "rxconfig.py").exists():
        app_dir = package_dir
    elif (package_dir.parent / "rxconfig.py").exists():
        app_dir = package_dir.parent
    else:
        print(
            "Error: Could not find rxconfig.py. "
            "Please run from the app directory or ensure the package is properly installed.",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = ["reflex", "run"]

    try:
        result = subprocess.run(cmd, cwd=app_dir, shell=False, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(
            "Error: 'reflex' command not found. "
            "Please ensure reflex is installed (pip install reflex).",
            file=sys.stderr,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
